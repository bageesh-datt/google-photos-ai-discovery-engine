import os
import json
import uuid
import asyncio
import threading
from typing import Dict, Any, Optional, List

from backend.app.config import settings
from backend.app.services.ingestion import load_raw_dataset
from backend.app.services.relevance import filter_relevance
from backend.app.services.extraction import extract_structured_observations
from backend.app.models.observation import StructuredObservation
from backend.app.models.cluster import ProblemCluster
from backend.app.models.opportunity import OpportunityArea
from backend.app.services.clustering import cluster_observations, is_valid_retrieval_observation
from backend.app.services.opportunities import synthesize_opportunities
from backend.app.models.analysis import (
    AnalysisStatusResponse,
    AnalysisExportResponse,
)

# In-memory status cache for quick status polling
STATUS_CACHE: Dict[str, AnalysisStatusResponse] = {}

# In-memory pipeline results store for fast polling and serverless compatibility
RESULTS_CACHE: Dict[str, Dict[str, Any]] = {}


def validate_current_analysis_evidence(
    clusters: List[ProblemCluster],
    opportunities: List[OpportunityArea],
    current_observations: List[StructuredObservation]
) -> Dict[str, Any]:
    """
    Strict evidence validation function:
    Verifies that zero stale/invalid evidence IDs leak into current results.
    Must verify:
    - no cluster contains an ID outside current dataset
    - no opportunity contains an ID outside current dataset
    - no duplicate evidence IDs within any cluster
    - every valid retrieval observation is either clustered or explicitly excluded
    - no excluded/Other/Low-evidence observation appears in a cluster
    - opportunity evidence is a subset of cluster evidence
    - no previous-analysis ID can leak into current results
    Returns metrics dict or raises ValueError if validation fails.
    """
    current_dataset_ids = set(o.id for o in current_observations)
    
    eligible_ids = set(
        o.id for o in current_observations
        if is_valid_retrieval_observation(o)
    )
    excluded_ids = current_dataset_ids - eligible_ids

    clustered_evidence_set = set()
    invalid_cluster_ids = []
    excluded_in_clusters = []
    duplicate_cluster_ids = []

    for c in clusters:
        seen_in_cluster = set()
        for eid in c.supporting_observation_ids:
            if eid in seen_in_cluster:
                duplicate_cluster_ids.append((c.cluster_id, eid))
            seen_in_cluster.add(eid)

            if eid not in current_dataset_ids:
                invalid_cluster_ids.append((c.cluster_id, eid))
            if eid in excluded_ids:
                excluded_in_clusters.append((c.cluster_id, eid))
            clustered_evidence_set.add(eid)

    opportunity_evidence_set = set()
    invalid_opp_ids = []
    opp_ids_not_in_clusters = []

    for opp in opportunities:
        for eid in opp.supporting_evidence_ids:
            if eid not in current_dataset_ids:
                invalid_opp_ids.append((opp.opportunity_id, eid))
            if eid not in clustered_evidence_set:
                opp_ids_not_in_clusters.append((opp.opportunity_id, eid))
            opportunity_evidence_set.add(eid)

    stale_cluster_ids = [eid for _, eid in invalid_cluster_ids]
    stale_opp_ids = [eid for _, eid in invalid_opp_ids]
    total_stale_count = len(stale_cluster_ids) + len(stale_opp_ids)

    unclustered_eligible = eligible_ids - clustered_evidence_set
    coverage_pct = 100.0 if not eligible_ids else ((len(eligible_ids) - len(unclustered_eligible)) / len(eligible_ids)) * 100.0

    metrics = {
        "input_observations": len(current_observations),
        "current_dataset_ids": len(current_dataset_ids),
        "valid_retrieval_observations": len(eligible_ids),
        "excluded_observations": len(excluded_ids),
        "clustered_evidence": len(clustered_evidence_set),
        "opportunity_evidence": len(opportunity_evidence_set),
        "invalid_stale_evidence_ids": total_stale_count,
        "stale_evidence_leakage": total_stale_count,
        "evidence_coverage": coverage_pct
    }

    if total_stale_count > 0:
        raise ValueError(
            f"EVIDENCE VALIDATION FAILED! Found {total_stale_count} stale/invalid evidence IDs outside current dataset: "
            f"Cluster stale: {invalid_cluster_ids}, Opportunity stale: {invalid_opp_ids}"
        )

    if excluded_in_clusters:
        raise ValueError(
            f"EVIDENCE VALIDATION FAILED! Excluded/Low/Other observations found in clusters: {excluded_in_clusters}"
        )

    if opp_ids_not_in_clusters:
        raise ValueError(
            f"EVIDENCE VALIDATION FAILED! Opportunity evidence IDs not present in clusters: {opp_ids_not_in_clusters}"
        )

    if duplicate_cluster_ids:
        raise ValueError(
            f"EVIDENCE VALIDATION FAILED! Duplicate evidence IDs in cluster: {duplicate_cluster_ids}"
        )

    if unclustered_eligible:
        raise ValueError(
            f"EVIDENCE VALIDATION FAILED! {len(unclustered_eligible)} eligible retrieval observations were not clustered: {unclustered_eligible}"
        )

    return metrics


def update_status(
    analysis_id: str,
    dataset_id: str,
    stage: str,
    progress_pct: int,
    status: str,
    total_obs: int = 0,
    relevant_obs: int = 0,
    clusters_cnt: int = 0,
    opps_cnt: int = 0,
    error_msg: Optional[str] = None
) -> AnalysisStatusResponse:
    status_resp = AnalysisStatusResponse(
        analysis_id=analysis_id,
        dataset_id=dataset_id,
        stage=stage,
        progress_pct=progress_pct,
        status=status,
        total_observations=total_obs,
        relevant_observations_count=relevant_obs,
        clusters_count=clusters_cnt,
        opportunities_count=opps_cnt,
        error_message=error_msg
    )
    STATUS_CACHE[analysis_id] = status_resp
    
    # Save status file on disk safely
    try:
        status_file = os.path.join(settings.OUTPUT_DIR, "observations", f"{analysis_id}_status.json")
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            f.write(status_resp.model_dump_json(indent=2))
    except Exception:
        pass
        
    return status_resp


def get_pipeline_status(analysis_id: str) -> AnalysisStatusResponse:
    if analysis_id in STATUS_CACHE:
        return STATUS_CACHE[analysis_id]
        
    status_file = os.path.join(settings.OUTPUT_DIR, "observations", f"{analysis_id}_status.json")
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            status_obj = AnalysisStatusResponse(**data)
            STATUS_CACHE[analysis_id] = status_obj
            return status_obj
            
    raise FileNotFoundError(f"Analysis with ID '{analysis_id}' not found.")


def run_discovery_pipeline_sync(analysis_id: str, dataset_id: str):
    """Executes the full 5-stage AI discovery pipeline synchronously."""
    try:
        # Stage 1: Load Ingested Raw Dataset
        update_status(analysis_id, dataset_id, "Stage 1: Dataset Validation & Loading", 10, "processing")
        raw_dataset = load_raw_dataset(dataset_id)
        total_obs = raw_dataset.valid_rows_count
        
        if total_obs == 0:
            raise ValueError(f"Dataset '{dataset_id}' contains 0 valid observations.")

        # Stage 2: AI Relevance Filtering
        def stage2_progress(done: int, total: int):
            pct = int(10 + (done / max(1, total)) * 20)
            update_status(
                analysis_id, dataset_id,
                f"Stage 2: processing {done}/{total}",
                pct, "processing", total_obs=total_obs
            )

        # Stage 2: AI Relevance Filtering
        update_status(analysis_id, dataset_id, f"Stage 2: processing 0/{total_obs}", 10, "processing", total_obs=total_obs)
        relevance_results = filter_relevance(raw_dataset.records, progress_callback=stage2_progress)
        relevance_map = {r.id: r for r in relevance_results}
        relevant_count = sum(1 for r in relevance_results if r.relevant)

        # Stage 3: LLM Structured 14-Field Extraction
        def stage3_progress(done: int, total: int):
            pct = int(30 + (done / max(1, total)) * 40)
            stage_str = f"Stage 3: processing {done}/{total}"
            print(stage_str, flush=True)
            update_status(
                analysis_id, dataset_id,
                stage_str,
                pct, "processing",
                total_obs=total_obs, relevant_obs=relevant_count
            )

        update_status(
            analysis_id, dataset_id, f"Stage 3: processing 0/{total_obs}", 30, "processing",
            total_obs=total_obs, relevant_obs=relevant_count
        )
        structured_obs = extract_structured_observations(
            raw_dataset.records,
            relevance_map=relevance_map,
            progress_callback=stage3_progress
        )

        valid_relevant_count = sum(1 for o in structured_obs if is_valid_retrieval_observation(o))

        # Stage 4: Semantic Problem Clustering
        update_status(
            analysis_id, dataset_id, "Stage 4: Semantic Problem Clustering", 75, "processing",
            total_obs=total_obs, relevant_obs=valid_relevant_count
        )
        clusters = cluster_observations(structured_obs)

        # Stage 5: Opportunity Area Synthesis
        update_status(
            analysis_id, dataset_id, "Stage 5: Opportunity Area Synthesis", 90, "processing",
            total_obs=total_obs, relevant_obs=valid_relevant_count, clusters_cnt=len(clusters)
        )
        opportunities = synthesize_opportunities(clusters)

        # Stage 6: Final Evidence & Integrity Audit
        update_status(
            analysis_id, dataset_id, "Stage 6: Final Integrity Audit", 95, "processing",
            total_obs=total_obs, relevant_obs=valid_relevant_count, clusters_cnt=len(clusters), opps_cnt=len(opportunities)
        )
        audit_metrics = validate_current_analysis_evidence(clusters, opportunities, structured_obs)
        print(f"[{analysis_id}] Pipeline Evidence Audit Passed: {json.dumps(audit_metrics)}", flush=True)

        # Cache results in memory
        RESULTS_CACHE[analysis_id] = {
            "observations": [o.model_dump() for o in structured_obs],
            "clusters": [c.model_dump() for c in clusters],
            "opportunities": [opp.model_dump() for opp in opportunities]
        }

        # Save files to disk safely if filesystem is writable
        try:
            obs_file = os.path.join(settings.OUTPUT_DIR, "observations", f"{analysis_id}.json")
            clusters_file = os.path.join(settings.OUTPUT_DIR, "clusters", f"{analysis_id}.json")
            opps_file = os.path.join(settings.OUTPUT_DIR, "opportunities", f"{analysis_id}.json")
            
            os.makedirs(os.path.dirname(obs_file), exist_ok=True)
            os.makedirs(os.path.dirname(clusters_file), exist_ok=True)
            os.makedirs(os.path.dirname(opps_file), exist_ok=True)

            with open(obs_file, "w", encoding="utf-8") as f:
                json.dump([o.model_dump() for o in structured_obs], f, indent=2)
            with open(clusters_file, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in clusters], f, indent=2)
            with open(opps_file, "w", encoding="utf-8") as f:
                json.dump([opp.model_dump() for opp in opportunities], f, indent=2)
        except Exception:
            pass

        # Complete pipeline execution
        update_status(
            analysis_id, dataset_id, "Completed", 100, "completed",
            total_obs=total_obs, relevant_obs=valid_relevant_count,
            clusters_cnt=len(clusters), opps_cnt=len(opportunities)
        )

    except Exception as e:
        update_status(
            analysis_id, dataset_id, "Pipeline Error", 0, "failed", error_msg=str(e)
        )


def start_pipeline_job(dataset_id: str) -> str:
    """Creates a new analysis_id and launches pipeline task."""
    analysis_id = f"analysis-{uuid.uuid4().hex[:8]}"
    update_status(analysis_id, dataset_id, "Initializing Pipeline", 0, "processing")
    
    # In Vercel serverless environments, execute synchronously to prevent background thread cancellation
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV") or os.environ.get("SYNC_PIPELINE") == "1":
        run_discovery_pipeline_sync(analysis_id, dataset_id)
    else:
        thread = threading.Thread(target=run_discovery_pipeline_sync, args=(analysis_id, dataset_id), daemon=True)
        thread.start()
    
    return analysis_id



def build_export_report(analysis_id: str) -> AnalysisExportResponse:
    """Builds complete export report with full evidence traceability mapping."""
    status_info = get_pipeline_status(analysis_id)
    
    observations = []
    clusters = []
    opportunities = []

    if analysis_id in RESULTS_CACHE:
        cached = RESULTS_CACHE[analysis_id]
        observations = cached.get("observations", [])
        clusters = cached.get("clusters", [])
        opportunities = cached.get("opportunities", [])
    else:
        obs_file = os.path.join(settings.OUTPUT_DIR, "observations", f"{analysis_id}.json")
        clusters_file = os.path.join(settings.OUTPUT_DIR, "clusters", f"{analysis_id}.json")
        opps_file = os.path.join(settings.OUTPUT_DIR, "opportunities", f"{analysis_id}.json")

        if os.path.exists(obs_file):
            with open(obs_file, "r", encoding="utf-8") as f:
                observations = json.load(f)
        if os.path.exists(clusters_file):
            with open(clusters_file, "r", encoding="utf-8") as f:
                clusters = json.load(f)
        if os.path.exists(opps_file):
            with open(opps_file, "r", encoding="utf-8") as f:
                opportunities = json.load(f)

    if observations:
        valid_relevant_count = sum(1 for o in observations if is_valid_retrieval_observation(o))
    else:
        valid_relevant_count = status_info.relevant_observations_count

    # Build bidirectional traceability map
    obs_dict = {o["id"]: o for o in observations}
    
    traceability_map: Dict[str, Dict[str, Any]] = {}
    
    for opp in opportunities:
        opp_id = opp["opportunity_id"]
        traceability_map[opp_id] = {
            "opportunity_name": opp["opportunity_name"],
            "supporting_clusters": [],
            "supporting_observations": []
        }
        
        # Link clusters
        for cl in clusters:
            overlap = set(cl["supporting_observation_ids"]).intersection(set(opp["supporting_evidence_ids"]))
            if overlap:
                traceability_map[opp_id]["supporting_clusters"].append({
                    "cluster_id": cl["cluster_id"],
                    "cluster_name": cl["cluster_name"],
                    "matched_observation_ids": list(overlap)
                })

        # Link observations & source URLs
        for obs_id in opp["supporting_evidence_ids"]:
            if obs_id in obs_dict:
                traceability_map[opp_id]["supporting_observations"].append({
                    "id": obs_id,
                    "source": obs_dict[obs_id]["source"],
                    "url": obs_dict[obs_id]["url"],
                    "retrieval_scenario": obs_dict[obs_id]["retrieval_scenario"],
                    "failure_point": obs_dict[obs_id]["failure_point"],
                    "problem_category": obs_dict[obs_id]["problem_category"]
                })

    return AnalysisExportResponse(
        analysis_id=analysis_id,
        dataset_id=status_info.dataset_id,
        total_observations=status_info.total_observations,
        relevant_count=valid_relevant_count,
        observations=observations,
        clusters=clusters,
        opportunities=opportunities,
        traceability_map=traceability_map
    )

