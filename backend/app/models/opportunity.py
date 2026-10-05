from typing import List
from pydantic import BaseModel, Field

class OpportunityArea(BaseModel):
    opportunity_id: str = Field(..., description="Unique opportunity code e.g. OPP-01")
    opportunity_name: str = Field(..., description="Broad research problem area title")
    user_problem: str = Field(..., description="Detailed explanation of user retrieval friction")
    supporting_evidence_ids: List[str] = Field(..., description="Linked observation IDs from underlying clusters")
    retrieval_stage: str = Field(..., description="Affected retrieval stage e.g. Memory Expression, Search Refinement")
    why_current_workaround_is_insufficient: str = Field(..., description="Friction analysis of workarounds")
    what_needs_to_be_validated: List[str] = Field(..., description="Hypotheses for 5-6 qualitative user interviews")
