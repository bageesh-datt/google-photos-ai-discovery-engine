import json
from typing import List
from backend.app.models.cluster import ProblemCluster
from backend.app.models.opportunity import OpportunityArea
from backend.app.prompts.opportunity_prompt import get_opportunity_prompt
from backend.app.services.llm_client import llm_client

def synthesize_opportunities_fallback(clusters: List[ProblemCluster]) -> List[OpportunityArea]:
    opportunities: List[OpportunityArea] = []
    
    for idx, cluster in enumerate(clusters, start=1):
        opp_id = f"OPP-{idx:02d}"
        c_name = cluster.cluster_name.lower()
        
        if "temporal" in c_name or "date" in c_name:
            opportunities.append(OpportunityArea(
                opportunity_id=opp_id,
                opportunity_name="Opportunity to improve retrieval when user memory is relative rather than exact",
                user_problem="Users remember general timeframes or relative context (e.g. 'July 2016' or 'a few years ago') but exact date-based indexing queries fail or return unhelpful chronological gaps.",
                supporting_evidence_ids=cluster.supporting_observation_ids,
                retrieval_stage="Memory Expression & Date Filtering",
                why_current_workaround_is_insufficient="Manual timeline scrolling across thousands of photos creates heavy cognitive load and user fatigue when temporal queries fail.",
                what_needs_to_be_validated=[
                    "How accurately do users remember the approximate timeframe of forgotten photos?",
                    "Whether soft/fuzzy temporal ranges match user memory better than rigid date filters.",
                    "How users react when a date search returns zero results vs approximate matches."
                ]
            ))
        elif "ocr" in c_name or "text" in c_name:
            opportunities.append(OpportunityArea(
                opportunity_id=opp_id,
                opportunity_name="Opportunity to surface documents and visual text through recognized in-image content",
                user_problem="Users remember specific words or headers contained inside captured documents, recipes, or slides, but current text search fails to surface matching photos.",
                supporting_evidence_ids=cluster.supporting_observation_ids,
                retrieval_stage="Search Understanding & Text OCR Indexing",
                why_current_workaround_is_insufficient="Manually searching through screenshot and document albums requires visually scanning dozens of thumbnails.",
                what_needs_to_be_validated=[
                    "What types of text-heavy photos (recipes, receipts, slides) are most frequently lost?",
                    "How users describe text appearing inside images when trying to locate them."
                ]
            ))
        elif "navigation" in c_name or "album" in c_name or "sync" in c_name:
            opportunities.append(OpportunityArea(
                opportunity_id=opp_id,
                opportunity_name="Improving retrieval when newly created albums are not immediately searchable",
                user_problem="Users expect a newly created album to become searchable immediately, but indexing/sync delays can create a gap between album creation and search availability.",
                supporting_evidence_ids=cluster.supporting_observation_ids,
                retrieval_stage="Album Indexing & Search Availability",
                why_current_workaround_is_insufficient="Users have to wait, refresh repeatedly, or manually navigate through the album list instead of finding the album through search.",
                what_needs_to_be_validated=[
                    "How quickly users expect a newly created album to appear in search.",
                    "How often users retry search when the album is not immediately available.",
                    "Whether users understand that indexing/sync may be delayed."
                ]
            ))
        else:
            opportunities.append(OpportunityArea(
                opportunity_id=opp_id,
                opportunity_name="Opportunity to assist retrieval when visual concept queries return incomplete photo sets",
                user_problem="Users search by familiar visual concepts or filenames, but indexing limitations return truncated or irrelevant subsets.",
                supporting_evidence_ids=cluster.supporting_observation_ids,
                retrieval_stage="Result Relevance & Search Refinement",
                why_current_workaround_is_insufficient="Users are forced to give up search entirely or try random keyword variations without guidance.",
                what_needs_to_be_validated=[
                    "How users attempt to refine broad keyword searches when results are incomplete.",
                    "What visual cues users expect to be indexed for complex photo memories."
                ]
            ))
            
    return opportunities


def validate_and_repair_opportunity_coverage(
    clusters: List[ProblemCluster],
    opportunities: List[OpportunityArea]
) -> List[OpportunityArea]:
    if not clusters or not opportunities:
        return opportunities
        
    all_cluster_obs_ids = set()
    for c in clusters:
        all_cluster_obs_ids.update(c.supporting_observation_ids)
        
    fallback_titles = [
        "Opportunity to improve retrieval when user memory is relative rather than exact",
        "Opportunity to surface documents and visual text through recognized in-image content",
        "Opportunity to assist retrieval when visual concept queries return incomplete photo sets",
        "Improving retrieval when newly created albums are not immediately searchable"
    ]
    
    repaired_opps = []
    seen_titles = set()
    
    for idx, opp in enumerate(opportunities):
        corresponding_cluster = clusters[idx] if idx < len(clusters) else None
        
        if corresponding_cluster:
            cluster_set = set(corresponding_cluster.supporting_observation_ids)
            ev_ids = [eid for eid in opp.supporting_evidence_ids if eid in cluster_set]
            for cid in corresponding_cluster.supporting_observation_ids:
                if cid not in ev_ids:
                    ev_ids.append(cid)
        else:
            ev_ids = [eid for eid in opp.supporting_evidence_ids if eid in all_cluster_obs_ids]
                    
        title = opp.opportunity_name.strip()
        if not title or title.lower() in seen_titles:
            title = fallback_titles[idx] if idx < len(fallback_titles) else f"Opportunity Area {idx+1}"
            
        seen_titles.add(title.lower())
        
        repaired_opps.append(OpportunityArea(
            opportunity_id=opp.opportunity_id or f"OPP-{idx+1:02d}",
            opportunity_name=title,
            user_problem=opp.user_problem,
            supporting_evidence_ids=ev_ids,
            retrieval_stage=opp.retrieval_stage,
            why_current_workaround_is_insufficient=opp.why_current_workaround_is_insufficient,
            what_needs_to_be_validated=opp.what_needs_to_be_validated
        ))
        
    # Verify every observation ID represented in cluster layer is present in at least one opportunity
    opp_covered_ids = set()
    for opp in repaired_opps:
        opp_covered_ids.update(opp.supporting_evidence_ids)
        
    missing_from_opps = all_cluster_obs_ids - opp_covered_ids
    if missing_from_opps and repaired_opps:
        for missing_id in missing_from_opps:
            for idx, c in enumerate(clusters):
                if missing_id in c.supporting_observation_ids and idx < len(repaired_opps):
                    if missing_id not in repaired_opps[idx].supporting_evidence_ids:
                        repaired_opps[idx].supporting_evidence_ids.append(missing_id)
                        
    return repaired_opps


def synthesize_opportunities(clusters: List[ProblemCluster]) -> List[OpportunityArea]:
    if not clusters:
        return []
        
    fallback = synthesize_opportunities_fallback(clusters)
    
    if not llm_client.api_key or llm_client.api_key.strip() in ("", "your_api_key_here", "dummy"):
        return validate_and_repair_opportunity_coverage(clusters, fallback)
        
    clusters_summary = [
        {
            "cluster_id": c.cluster_id,
            "cluster_name": c.cluster_name,
            "core_problem": c.core_problem,
            "supporting_observation_ids": c.supporting_observation_ids
        }
        for c in clusters
    ]
    prompt = get_opportunity_prompt(json.dumps(clusters_summary, indent=2))
    
    try:
        json_output = llm_client.generate_json(prompt, mock_fallback=[o.model_dump() for o in fallback])
        if isinstance(json_output, list) and len(json_output) == len(clusters):
            valid_opps = []
            seen_names = set()
            
            for idx, (item, cluster) in enumerate(zip(json_output, clusters)):
                opp_id = f"OPP-{idx+1:02d}"
                raw_ev_ids = list(item.get("supporting_evidence_ids", []))
                
                # Filter evidence IDs strictly to cluster observations
                cluster_obs_set = set(cluster.supporting_observation_ids)
                valid_ev_ids = [eid for eid in raw_ev_ids if eid in cluster_obs_set]
                
                # Merge in any missing observation IDs from the parent cluster
                for cid in cluster.supporting_observation_ids:
                    if cid not in valid_ev_ids:
                        valid_ev_ids.append(cid)
                    
                opp_name = str(item.get("opportunity_name", "")).strip()
                
                if not opp_name or opp_name.lower() in seen_names:
                    opp_name = fallback[idx].opportunity_name
                    
                seen_names.add(opp_name.lower())

                valid_opps.append(OpportunityArea(
                    opportunity_id=str(item.get("opportunity_id", opp_id)),
                    opportunity_name=opp_name,
                    user_problem=str(item.get("user_problem", fallback[idx].user_problem)),
                    supporting_evidence_ids=valid_ev_ids,
                    retrieval_stage=str(item.get("retrieval_stage", fallback[idx].retrieval_stage)),
                    why_current_workaround_is_insufficient=str(
                        item.get("why_current_workaround_is_insufficient", fallback[idx].why_current_workaround_is_insufficient)
                    ),
                    what_needs_to_be_validated=list(
                        item.get("what_needs_to_be_validated", fallback[idx].what_needs_to_be_validated)
                    )
                ))
                
            return validate_and_repair_opportunity_coverage(clusters, valid_opps)
        return validate_and_repair_opportunity_coverage(clusters, fallback)
    except Exception:
        return validate_and_repair_opportunity_coverage(clusters, fallback)


