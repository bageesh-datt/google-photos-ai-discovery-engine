from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

from backend.app.models.observation import StructuredObservation
from backend.app.models.cluster import ProblemCluster
from backend.app.models.opportunity import OpportunityArea

class RelevanceResult(BaseModel):
    id: str
    relevant: bool
    reason: str

class AnalysisStartRequest(BaseModel):
    dataset_id: str

class AnalysisStartResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    status: str
    message: str

class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    stage: str
    progress_pct: int
    status: Literal["pending", "processing", "completed", "failed"]
    total_observations: int = 0
    relevant_observations_count: int = 0
    clusters_count: int = 0
    opportunities_count: int = 0
    error_message: Optional[str] = None

class AnalysisExportResponse(BaseModel):
    analysis_id: str
    dataset_id: str
    total_observations: int
    relevant_count: int
    observations: List[StructuredObservation]
    clusters: List[ProblemCluster]
    opportunities: List[OpportunityArea]
    traceability_map: Dict[str, Dict[str, Any]]
