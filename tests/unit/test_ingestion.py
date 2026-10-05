import os
import pytest
from backend.app.services.ingestion import (
    parse_and_validate_csv_content,
    load_preset_pilot_dataset,
    load_raw_dataset,
)

SAMPLE_VALID_CSV = """id,source,url,user_statement,retrieval_scenario
R99,Reddit,https://reddit.com/r/test/1,"Searching for my dog photo from 2021",Find dog photo
R100,Reddit,https://reddit.com/r/test/2,"Looking for old invoice screenshot",Find invoice screenshot
"""

SAMPLE_MISSING_HEADER_CSV = """id,source,url,user_statement
R99,Reddit,https://reddit.com/r/test/1,"Searching for my dog photo"
"""

SAMPLE_INVALID_URL_CSV = """id,source,url,user_statement,retrieval_scenario
R99,Reddit,not_a_valid_url,"Searching for my dog photo",Find dog photo
"""

SAMPLE_DUPLICATE_ID_CSV = """id,source,url,user_statement,retrieval_scenario
R99,Reddit,https://reddit.com/r/test/1,"Searching for my dog photo",Find dog photo
R99,Reddit,https://reddit.com/r/test/2,"Duplicate entry with same ID",Find dog photo
"""

def test_valid_csv_parsing():
    response = parse_and_validate_csv_content(SAMPLE_VALID_CSV, dataset_id_override="test-valid-1")
    assert response.dataset_id == "test-valid-1"
    assert response.total_rows == 2
    assert response.valid_rows_count == 2
    assert response.invalid_rows_count == 0
    assert len(response.records) == 2
    assert response.records[0].id == "R99"
    assert response.records[1].id == "R100"


def test_missing_required_headers():
    with pytest.raises(ValueError) as exc_info:
        parse_and_validate_csv_content(SAMPLE_MISSING_HEADER_CSV)
    assert "Missing required CSV columns" in str(exc_info.value)
    assert "retrieval_scenario" in str(exc_info.value)


def test_invalid_url_handling():
    response = parse_and_validate_csv_content(SAMPLE_INVALID_URL_CSV, dataset_id_override="test-invalid-url")
    assert response.total_rows == 1
    assert response.valid_rows_count == 0
    assert response.invalid_rows_count == 1
    assert response.validation_errors[0].error_type == "VALIDATION_ERROR"
    assert "not a valid HTTP or HTTPS URL" in response.validation_errors[0].message


def test_duplicate_id_handling():
    response = parse_and_validate_csv_content(SAMPLE_DUPLICATE_ID_CSV, dataset_id_override="test-dup-id")
    assert response.total_rows == 2
    assert response.valid_rows_count == 1
    assert response.invalid_rows_count == 1
    assert response.validation_errors[0].error_type == "DUPLICATE_ID"
    assert "Duplicate observation ID 'R99'" in response.validation_errors[0].message


def test_preset_pilot_dataset_loading():
    response = load_preset_pilot_dataset()
    assert response.dataset_id == "preset-pilot-v1"
    assert response.total_rows == 12
    assert response.valid_rows_count == 12
    assert response.invalid_rows_count == 0
    assert len(response.records) == 12
    assert response.records[0].id == "R01"
    assert response.records[11].id == "GS05"


def test_raw_dataset_persistence_and_loading():
    response = parse_and_validate_csv_content(SAMPLE_VALID_CSV, dataset_id_override="test-persist-1")
    loaded_response = load_raw_dataset("test-persist-1")
    assert loaded_response.dataset_id == "test-persist-1"
    assert loaded_response.valid_rows_count == 2
    assert loaded_response.records[0].id == "R99"
