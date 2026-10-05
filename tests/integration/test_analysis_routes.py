import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

from unittest.mock import patch

def test_full_pipeline_api_lifecycle():
    with patch("backend.app.services.llm_client.LLMClient.generate_json", side_effect=lambda prompt, mock_fallback=None: mock_fallback):
        # 1. Load preset pilot dataset to get dataset_id
        preset_resp = client.get("/api/datasets/preset")
        assert preset_resp.status_code == 200
        dataset_id = preset_resp.json()["dataset_id"]
        
        # 2. Start pipeline analysis
        start_resp = client.post("/api/analysis/start", json={"dataset_id": dataset_id})
        assert start_resp.status_code == 202
        analysis_id = start_resp.json()["analysis_id"]
        assert analysis_id.startswith("analysis-")

        # 3. Poll status until completed (or timeout after 10s)
        completed = False
        for _ in range(30):
            status_resp = client.get(f"/api/analysis/{analysis_id}/status")
            assert status_resp.status_code == 200
            data = status_resp.json()
            if data["status"] == "completed":
                completed = True
                break
            time.sleep(0.1)
            
        assert completed is True, "Pipeline execution did not complete within timeout"

    # 4. Fetch observations
    obs_resp = client.get(f"/api/analysis/{analysis_id}/observations")
    assert obs_resp.status_code == 200
    observations = obs_resp.json()
    assert len(observations) > 0
    assert "id" in observations[0]
    assert "problem_category" in observations[0]

    # 5. Fetch clusters
    clusters_resp = client.get(f"/api/analysis/{analysis_id}/clusters")
    assert clusters_resp.status_code == 200
    clusters = clusters_resp.json()
    assert len(clusters) > 0
    assert "supporting_observation_ids" in clusters[0]

    # 6. Fetch opportunities
    opps_resp = client.get(f"/api/analysis/{analysis_id}/opportunities")
    assert opps_resp.status_code == 200
    opportunities = opps_resp.json()
    assert len(opportunities) > 0
    assert "supporting_evidence_ids" in opportunities[0]

    # 7. Fetch export report and verify evidence traceability
    export_resp = client.get(f"/api/analysis/{analysis_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert export_data["analysis_id"] == analysis_id
    assert "traceability_map" in export_data
    assert len(export_data["traceability_map"]) > 0


def test_start_analysis_nonexistent_dataset():
    response = client.post("/api/analysis/start", json={"dataset_id": "nonexistent-dataset-id"})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_nonexistent_analysis_status():
    response = client.get("/api/analysis/nonexistent-analysis-id/status")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
