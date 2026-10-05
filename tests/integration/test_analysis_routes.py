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


def test_serverless_cold_start_pilot_fallback():
    from backend.app.services.pipeline import RESULTS_CACHE, STATUS_CACHE
    
    # 1. Clear in-memory caches to simulate serverless cold-start / instance switch
    RESULTS_CACHE.clear()
    STATUS_CACHE.clear()
    
    pilot_analysis_id = "analysis-pilot-coldstart-test123"
    
    # 2. Status check must succeed via fallback
    status_resp = client.get(f"/api/analysis/{pilot_analysis_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"
    
    # 3. Observations endpoint must return 12 records
    obs_resp = client.get(f"/api/analysis/{pilot_analysis_id}/observations")
    assert obs_resp.status_code == 200
    assert len(obs_resp.json()) == 12
    
    # 4. Clusters endpoint must return 4 clusters
    clusters_resp = client.get(f"/api/analysis/{pilot_analysis_id}/clusters")
    assert clusters_resp.status_code == 200
    assert len(clusters_resp.json()) == 4
    
    # 5. Opportunities endpoint must return 4 opportunities
    opps_resp = client.get(f"/api/analysis/{pilot_analysis_id}/opportunities")
    assert opps_resp.status_code == 200
    assert len(opps_resp.json()) == 4
    
    # 6. Export endpoint must build complete report with traceability map
    export_resp = client.get(f"/api/analysis/{pilot_analysis_id}/export")
    assert export_resp.status_code == 200
    assert export_resp.json()["total_observations"] == 12
    assert len(export_resp.json()["traceability_map"]) > 0


def test_unknown_analysis_returns_404_across_all_endpoints():
    from backend.app.services.pipeline import RESULTS_CACHE, STATUS_CACHE
    RESULTS_CACHE.clear()
    STATUS_CACHE.clear()
    
    non_pilot_ids = [
        "analysis-nonexistent-unknown-999",
        "random-pilot-test",
        "analysis-custom-pilot-123",
    ]
    
    for unknown_id in non_pilot_ids:
        assert client.get(f"/api/analysis/{unknown_id}/status").status_code == 404
        assert client.get(f"/api/analysis/{unknown_id}/observations").status_code == 404
        assert client.get(f"/api/analysis/{unknown_id}/clusters").status_code == 404
        assert client.get(f"/api/analysis/{unknown_id}/opportunities").status_code == 404
        assert client.get(f"/api/analysis/{unknown_id}/export").status_code == 404


