import csv
import io
import json
import os
import uuid
from typing import Tuple, List, Dict, Any, Union

from backend.app.config import settings
from backend.app.models.dataset import (
    RawObservation,
    ValidationErrorDetail,
    DatasetUploadResponse,
)

REQUIRED_COLUMNS = {"id", "source", "url", "user_statement", "retrieval_scenario"}

def parse_and_validate_csv_content(
    file_content: str,
    dataset_id_override: str = None
) -> DatasetUploadResponse:
    """
    Parses CSV content string, validates required columns, validates row-level data,
    deduplicates by ID, and returns a DatasetUploadResponse.
    """
    reader = csv.DictReader(io.StringIO(file_content))
    
    # Check headers
    if not reader.fieldnames:
        raise ValueError("Uploaded CSV file is empty or missing header row.")
    
    found_headers = set(name.strip().lower() for name in reader.fieldnames if name)
    missing_headers = REQUIRED_COLUMNS - found_headers
    if missing_headers:
        raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing_headers))}")

    valid_records: List[RawObservation] = []
    validation_errors: List[ValidationErrorDetail] = []
    seen_ids: Dict[str, int] = {}
    
    row_count = 0
    for idx, row in enumerate(reader, start=1):
        row_count += 1
        # Normalize keys (strip whitespace)
        normalized_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
        
        obs_id = normalized_row.get("id", "")
        
        # Check duplicate ID within dataset
        if obs_id and obs_id in seen_ids:
            validation_errors.append(
                ValidationErrorDetail(
                    row_index=idx,
                    observation_id=obs_id,
                    error_type="DUPLICATE_ID",
                    message=f"Duplicate observation ID '{obs_id}' previously seen on row {seen_ids[obs_id]}."
                )
            )
            continue
            
        try:
            observation = RawObservation(
                id=normalized_row.get("id", ""),
                source=normalized_row.get("source", ""),
                url=normalized_row.get("url", ""),
                user_statement=normalized_row.get("user_statement", ""),
                retrieval_scenario=normalized_row.get("retrieval_scenario", "")
            )
            valid_records.append(observation)
            if obs_id:
                seen_ids[obs_id] = idx
        except Exception as e:
            validation_errors.append(
                ValidationErrorDetail(
                    row_index=idx,
                    observation_id=obs_id if obs_id else None,
                    error_type="VALIDATION_ERROR",
                    message=str(e)
                )
            )

    dataset_id = dataset_id_override if dataset_id_override else f"dataset-{uuid.uuid4().hex[:8]}"
    
    response = DatasetUploadResponse(
        dataset_id=dataset_id,
        total_rows=row_count,
        valid_rows_count=len(valid_records),
        invalid_rows_count=len(validation_errors),
        records=valid_records,
        validation_errors=validation_errors
    )
    
    # Save dataset to data/raw/{dataset_id}.json
    save_raw_dataset(response)
    
    return response


# In-memory dataset store for fast access and serverless compatibility
DATASET_CACHE: Dict[str, DatasetUploadResponse] = {}

def save_raw_dataset(dataset_response: DatasetUploadResponse) -> str:
    DATASET_CACHE[dataset_response.dataset_id] = dataset_response
    raw_dir = os.path.join(settings.DATA_DIR, "raw")
    filepath = os.path.join(raw_dir, f"{dataset_response.dataset_id}.json")
    try:
        os.makedirs(raw_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(dataset_response.model_dump_json(indent=2))
    except Exception:
        pass
    return filepath


def load_raw_dataset(dataset_id: str) -> DatasetUploadResponse:
    if dataset_id in DATASET_CACHE:
        return DATASET_CACHE[dataset_id]
        
    if dataset_id == "preset-pilot-v1":
        return load_preset_pilot_dataset()
        
    filepath = os.path.join(settings.DATA_DIR, "raw", f"{dataset_id}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset with ID '{dataset_id}' not found.")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        ds = DatasetUploadResponse(**data)
        DATASET_CACHE[dataset_id] = ds
        return ds


def load_preset_pilot_dataset() -> DatasetUploadResponse:
    if "preset-pilot-v1" in DATASET_CACHE:
        return DATASET_CACHE["preset-pilot-v1"]
        
    pilot_csv_path = os.path.join(settings.DATA_DIR, "sample_observations.csv")
    if not os.path.exists(pilot_csv_path):
        from backend.app.config import BASE_DIR
        pilot_csv_path = os.path.join(BASE_DIR, "data", "sample_observations.csv")

    if not os.path.exists(pilot_csv_path):
        raise FileNotFoundError(f"Pilot sample observations CSV not found at '{pilot_csv_path}'.")
    
    with open(pilot_csv_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return parse_and_validate_csv_content(content, dataset_id_override="preset-pilot-v1")


