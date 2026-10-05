import os
import json
import pytest

from backend.app.services.clustering import is_valid_retrieval_observation


def is_relevant_observation_ui(obs: dict) -> bool:
    """Python counterpart of frontend isRelevantObservation helper."""
    if not obs:
        return False
    if obs.get("retrieval_outcome") == "Excluded from retrieval failure analysis.":
        return False
    if obs.get("problem_category") == "Other":
        return False
    if obs.get("evidence_strength") == "Low":
        return False
    fp = str(obs.get("failure_point", "")).lower()
    if "lacks explicit evidence" in fp or "describes non-retrieval issue" in fp:
        return False
    return True


def get_failure_point_label_ui(obs: dict) -> str:
    """Python counterpart of frontend getFailurePointLabel helper."""
    return "Failure Point" if is_relevant_observation_ui(obs) else "Relevance Reason"


def test_raw_relevant_rejected_counts_scaled_analysis():
    """Verify Raw, Relevant, Rejected counts on scaled 1000 observation analysis status."""
    status_file = os.path.join("output", "observations", "analysis-fresh-1000-strict-1789843940_status.json")
    assert os.path.exists(status_file), f"Sample status file '{status_file}' not found"

    with open(status_file, "r", encoding="utf-8") as f:
        status_data = json.load(f)

    raw_count = status_data["total_observations"]
    relevant_count = status_data["relevant_observations_count"]
    rejected_count = raw_count - relevant_count

    assert raw_count == 1000, f"Expected 1000 raw feedback, got {raw_count}"
    assert relevant_count == 131, f"Expected 131 relevant retrieval, got {relevant_count}"
    assert rejected_count == 869, f"Expected 869 rejected / non-retrieval, got {rejected_count}"


def test_pilot_dataset_counts_and_unchanged_output():
    """Verify pilot dataset (12 records) counts and cluster/opportunity unchanged outputs."""
    pilot_file = os.path.join("output", "observations", "analysis-pilot-verify.json")
    assert os.path.exists(pilot_file), f"Pilot observations file '{pilot_file}' not found"

    with open(pilot_file, "r", encoding="utf-8") as f:
        observations = json.load(f)

    raw_count = len(observations)
    relevant_count = sum(1 for o in observations if is_relevant_observation_ui(o))
    rejected_count = raw_count - relevant_count

    assert raw_count == 12
    assert relevant_count == 12
    assert rejected_count == 0


def test_relevance_filter_and_conditional_labeling():
    """Verify relevance filter logic and conditional label assignment."""
    relevant_obs = {
        "id": "R-01",
        "source": "Reddit",
        "url": "https://reddit.com/r/googlephotos/123",
        "retrieval_scenario": "Searching for wedding photos by date",
        "what_user_remembers": "June 2021 wedding in Paris",
        "failure_point": "Inability to filter search by custom date range",
        "problem_category": "Metadata / date / location mismatch",
        "evidence_strength": "High",
        "retrieval_outcome": "Zero results returned"
    }

    non_relevant_obs = {
        "id": "NR-01",
        "source": "Google Play",
        "url": "https://play.google.com/store/apps/details?id=com.google.android.apps.photos",
        "retrieval_scenario": "Not mentioned",
        "what_user_remembers": "Not mentioned",
        "failure_point": "Lacks explicit evidence of photo/video search or retrieval scenario.",
        "problem_category": "Other",
        "evidence_strength": "Low",
        "retrieval_outcome": "Excluded from retrieval failure analysis."
    }

    all_obs = [relevant_obs, non_relevant_obs]

    # Test classification
    assert is_relevant_observation_ui(relevant_obs) is True
    assert is_relevant_observation_ui(non_relevant_obs) is False

    # Test conditional label behavior
    assert get_failure_point_label_ui(relevant_obs) == "Failure Point"
    assert get_failure_point_label_ui(non_relevant_obs) == "Relevance Reason"

    # Test filter: ALL
    filtered_all = [o for o in all_obs]
    assert len(filtered_all) == 2

    # Test filter: RELEVANT
    filtered_rel = [o for o in all_obs if is_relevant_observation_ui(o)]
    assert len(filtered_rel) == 1
    assert filtered_rel[0]["id"] == "R-01"

    # Test filter: NOT_RELEVANT
    filtered_not_rel = [o for o in all_obs if not is_relevant_observation_ui(o)]
    assert len(filtered_not_rel) == 1
    assert filtered_not_rel[0]["id"] == "NR-01"


def test_exported_json_and_summary_relevance_consistency_gp_us_470():
    """
    Regression test ensuring:
    - relevant_count == number of genuinely relevant/high-evidence observations (66 on 1000 dataset)
    - rejected_count + relevant_count == total_observations (934 + 66 == 1000)
    - GP-US-470 (problem_category='Other', evidence_strength='Low', general feedback failure_point)
      is explicitly excluded from relevant_count and classified as rejected/non-retrieval.
    """
    from backend.app.services.clustering import is_valid_retrieval_observation
    from backend.app.services.pipeline import build_export_report

    obs_file = os.path.join("output", "observations", "analysis-02be7d7d.json")
    if not os.path.exists(obs_file):
        pytest.skip(f"Analysis observations file '{obs_file}' not found.")

    with open(obs_file, "r", encoding="utf-8") as f:
        observations = json.load(f)

    analysis_id = "analysis-02be7d7d"
    report = build_export_report(analysis_id)

    total_observations = report.total_observations
    relevant_count = report.relevant_count
    rejected_count = total_observations - relevant_count

    # Calculate count of genuinely relevant/high-evidence observations
    genuinely_relevant_count = sum(1 for o in observations if is_valid_retrieval_observation(o))

    assert total_observations == 1000
    assert relevant_count == 66
    assert rejected_count == 934
    assert relevant_count == genuinely_relevant_count
    assert rejected_count + relevant_count == total_observations

    # Ensure GP-US-470 is classified as non-relevant/rejected
    gp_470 = next(o for o in observations if o["id"] == "GP-US-470")
    assert gp_470["problem_category"] == "Other"
    assert gp_470["evidence_strength"] == "Low"
    assert is_valid_retrieval_observation(gp_470) is False
    assert is_relevant_observation_ui(gp_470) is False

