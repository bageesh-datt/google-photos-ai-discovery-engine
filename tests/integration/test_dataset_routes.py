import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_preset_dataset_endpoint():
    response = client.get("/api/datasets/preset")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "preset-pilot-v1"
    assert data["total_rows"] == 12
    assert data["valid_rows_count"] == 12
    assert data["invalid_rows_count"] == 0
    assert len(data["records"]) == 12


def test_upload_dataset_endpoint_success():
    csv_content = (
        "id,source,url,user_statement,retrieval_scenario\n"
        "U01,Reddit,https://reddit.com/r/test/u1,\"Verbatim statement 1\",Scenario 1\n"
        "U02,PlayStore,https://play.google.com/store/apps/details?id=test,\"Verbatim statement 2\",Scenario 2\n"
    )
    files = {
        "file": ("test_upload.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    response = client.post("/api/datasets/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["total_rows"] == 2
    assert data["valid_rows_count"] == 2
    assert data["records"][0]["id"] == "U01"
    assert data["records"][1]["id"] == "U02"


def test_upload_dataset_endpoint_invalid_file_extension():
    files = {
        "file": ("test_upload.txt", io.BytesIO(b"random text"), "text/plain")
    }
    response = client.post("/api/datasets/upload", files=files)
    assert response.status_code == 400
    assert "Only CSV files (.csv) are accepted" in response.json()["detail"]


def test_upload_dataset_endpoint_invalid_csv_headers():
    csv_content = (
        "id,source,url\n"
        "U01,Reddit,https://reddit.com/r/test/u1\n"
    )
    files = {
        "file": ("invalid_headers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
    }
    response = client.post("/api/datasets/upload", files=files)
    assert response.status_code == 400
    assert "Missing required CSV columns" in response.json()["detail"]
