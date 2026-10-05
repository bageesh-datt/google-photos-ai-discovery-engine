from typing import List
from pydantic import BaseModel, Field

class ProblemCluster(BaseModel):
    cluster_id: str = Field(..., description="Unique cluster identifier e.g. CL-01")
    cluster_name: str = Field(..., description="Concise cluster title")
    core_problem: str = Field(..., description="Root retrieval failure description")
    supporting_observation_ids: List[str] = Field(..., description="Array of linked observation IDs e.g. ['R01', 'R05']")
    count: int = Field(..., description="Total supporting observation count")
    what_users_remember: str = Field(..., description="Common remembered elements across cluster")
    what_is_missing: str = Field(..., description="Common missing information across cluster")
    typical_search_behavior: str = Field(..., description="Dominant search pattern")
    failure_point: str = Field(..., description="Primary breakdown point")
    workarounds: str = Field(..., description="Summary of user workarounds")
    evidence_summary: str = Field(..., description="Summary grounded strictly in supporting evidence")
    open_questions_for_interviews: List[str] = Field(..., description="Targeted questions for 5-6 user interviews")
