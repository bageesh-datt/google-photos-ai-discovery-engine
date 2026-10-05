from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
import re

class RawObservation(BaseModel):
    id: str = Field(..., description="Unique observation code e.g. R01")
    source: str = Field(..., description="Source platform e.g. Reddit, PlayStore, GoogleSupport")
    url: str = Field(..., description="Verifiable public URL")
    user_statement: str = Field(..., description="Exact verbatim user quote")
    retrieval_scenario: str = Field(..., description="Contextual search scenario")

    @field_validator('id', 'source', 'user_statement', 'retrieval_scenario')
    @classmethod
    def check_non_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"Field '{info.field_name}' cannot be empty or whitespace.")
        return value.strip()

    @field_validator('url')
    @classmethod
    def check_url_format(cls, value: str) -> str:
        clean_url = value.strip()
        url_regex = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
        if not url_regex.match(clean_url):
            raise ValueError(f"URL '{clean_url}' is not a valid HTTP or HTTPS URL.")
        return clean_url


class ValidationErrorDetail(BaseModel):
    row_index: int
    observation_id: Optional[str] = None
    error_type: str
    message: str


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    records: List[RawObservation]
    validation_errors: List[ValidationErrorDetail]
