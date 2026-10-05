from typing import Literal
from pydantic import BaseModel, Field

TAXONOMY_CATEGORIES = [
    "Memory expression failure",
    "Search understanding failure",
    "Retrieval / indexing failure",
    "Result relevance failure",
    "Result evaluation failure",
    "Search refinement failure",
    "Navigation / browsing failure",
    "Metadata / date / location mismatch",
    "Other",
]

class StructuredObservation(BaseModel):
    id: str = Field(..., description="Original observation code e.g. R01")
    source: str = Field(..., description="Source platform e.g. Reddit, GoogleSupport")
    url: str = Field(..., description="Original verifiable source URL")
    retrieval_scenario: str = Field(..., description="Context/goal of user search")
    what_user_remembers: str = Field(..., description="Memory clues (visual, date, location, people)")
    what_user_forgot: str = Field(..., description="Forgotten metadata or context ('Not mentioned' if absent)")
    search_attempt: str = Field(..., description="Specific search term or filter used")
    search_behavior: str = Field(..., description="Pattern e.g., keyword tweaking, timeline scrolling")
    retrieval_outcome: str = Field(..., description="Result e.g., wrong photos, zero results, gave up")
    failure_point: str = Field(..., description="Exact breakdown point in search flow")
    workaround: str = Field(..., description="User workaround ('Not mentioned' if absent)")
    problem_category: str = Field(..., description="Standardized taxonomy category")
    evidence_strength: Literal["High", "Medium", "Low"] = Field(..., description="Directness of verbatim quote")
    analyst_note: str = Field(..., description="Objective extraction notes strictly grounded in quote")
