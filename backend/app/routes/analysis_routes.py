import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse, Response

from backend.app.config import settings
from backend.app.models.analysis import (
    AnalysisStartRequest,
    AnalysisStartResponse,
    AnalysisStatusResponse,
    AnalysisExportResponse,
)
from backend.app.models.observation import StructuredObservation
from backend.app.models.cluster import ProblemCluster
from backend.app.models.opportunity import OpportunityArea
from backend.app.services.ingestion import load_raw_dataset
from backend.app.services.pipeline import (
    start_pipeline_job,
    get_pipeline_status,
    build_export_report,
    RESULTS_CACHE,
)

router = APIRouter(prefix="/api/analysis", tags=["AI Discovery Pipeline"])

@router.post(
    "/start",
    response_model=AnalysisStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start AI Discovery Pipeline",
    description="Triggers the 5-stage AI discovery process for an ingested raw dataset."
)
async def start_analysis(payload: AnalysisStartRequest):
    try:
        load_raw_dataset(payload.dataset_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{payload.dataset_id}' not found. Please upload or load preset dataset first."
        )

    analysis_id = start_pipeline_job(payload.dataset_id)
    return AnalysisStartResponse(
        analysis_id=analysis_id,
        dataset_id=payload.dataset_id,
        status="processing",
        message="AI Discovery pipeline started successfully."
    )


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisStatusResponse,
    summary="Get Pipeline Progress Status",
    description="Returns real-time processing status, stage name, progress percentage, and item counts."
)
async def get_analysis_status(analysis_id: str):
    try:
        return get_pipeline_status(analysis_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{analysis_id}/observations",
    response_model=List[StructuredObservation],
    summary="Get Extracted Structured Observations",
    description="Returns extracted 14-field structured observations with optional category filtering."
)
async def get_analysis_observations(
    analysis_id: str,
    category: Optional[str] = Query(None, description="Optional taxonomy category filter")
):
    records = []
    if analysis_id in RESULTS_CACHE:
        records = RESULTS_CACHE[analysis_id].get("observations", [])
    else:
        obs_file = os.path.join(settings.OUTPUT_DIR, "observations", f"{analysis_id}.json")
        if not os.path.exists(obs_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Observations for analysis ID '{analysis_id}' not found. Pipeline may still be processing."
            )
        with open(obs_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        
    if category:
        records = [r for r in records if r.get("problem_category") == category]
        
    return records


@router.get(
    "/{analysis_id}/clusters",
    response_model=List[ProblemCluster],
    summary="Get Problem Clusters",
    description="Returns recurring problem pattern clusters with supporting observation IDs."
)
async def get_analysis_clusters(analysis_id: str):
    if analysis_id in RESULTS_CACHE:
        return RESULTS_CACHE[analysis_id].get("clusters", [])
        
    clusters_file = os.path.join(settings.OUTPUT_DIR, "clusters", f"{analysis_id}.json")
    if not os.path.exists(clusters_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clusters for analysis ID '{analysis_id}' not found. Pipeline may still be processing."
        )
        
    with open(clusters_file, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/{analysis_id}/opportunities",
    response_model=List[OpportunityArea],
    summary="Get Opportunity Areas",
    description="Returns potential research opportunity areas grounded in evidence."
)
async def get_analysis_opportunities(analysis_id: str):
    if analysis_id in RESULTS_CACHE:
        return RESULTS_CACHE[analysis_id].get("opportunities", [])
        
    opps_file = os.path.join(settings.OUTPUT_DIR, "opportunities", f"{analysis_id}.json")
    if not os.path.exists(opps_file):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunities for analysis ID '{analysis_id}' not found. Pipeline may still be processing."
        )
        
    with open(opps_file, "r", encoding="utf-8") as f:
        return json.load(f)



@router.get(
    "/{analysis_id}/export",
    response_model=AnalysisExportResponse,
    summary="Export Complete Analysis Report",
    description="Exports full report including observations, clusters, opportunities, and bidirectional evidence traceability map."
)
async def export_analysis_report(analysis_id: str):
    try:
        report = build_export_report(analysis_id)
        return report
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
