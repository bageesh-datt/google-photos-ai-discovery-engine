import pytest
from backend.app.models.dataset import RawObservation
from backend.app.services.relevance import evaluate_relevance_fallback
from backend.app.services.extraction import extract_observation_fallback


def test_generic_praise_false_positives():
    """Verify that positive reviews praising Google Photos remain non-relevant."""
    praise_statements = [
        "Google Photos is great and easy to use.",
        "Very very best and photo update this absolutely Google photos veri nice...",
        "Serves as a top-tier digital archive and secondary media backup solution.",
        "Google Photos is wonderful, I love having all my memories saved!",
        "Handy to have and very convenient."
    ]
    for stmt in praise_statements:
        obs = RawObservation(id="TEST-PRAISE", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
        result = evaluate_relevance_fallback(obs)
        assert result.relevant is False, f"False positive for praise statement: '{stmt}'"


def test_sharing_only_false_positives():
    """Verify that sharing-only complaints remain non-relevant."""
    sharing_statements = [
        "Partner sharing link isn't working when I send it to my wife.",
        "Can't share photos directly to Signal app.",
        "Sharing link generates an error message."
    ]
    for stmt in sharing_statements:
        obs = RawObservation(id="TEST-SHARE", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
        result = evaluate_relevance_fallback(obs)
        assert result.relevant is False, f"False positive for sharing statement: '{stmt}'"


def test_storage_only_false_positives():
    """Verify that storage pricing and Google One quota complaints remain non-relevant."""
    storage_statements = [
        "Google One 15GB storage is full, constantly nagging me to pay for more storage.",
        "Very loving towards family, but I'm being intimidated by Google to buy storage.",
        "Storage price is too high for cloud photos."
    ]
    for stmt in storage_statements:
        obs = RawObservation(id="TEST-STORAGE", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
        result = evaluate_relevance_fallback(obs)
        assert result.relevant is False, f"False positive for storage statement: '{stmt}'"


def test_backup_only_false_positives():
    """Verify that backup/sync complaints without photo retrieval failure remain non-relevant."""
    backup_statements = [
        "Constant nagging to use their backup service gets old and always comes back after an update.",
        "Auto backup uses too much mobile data when on cellular network.",
        "Backup is stuck at 50% uploading."
    ]
    for stmt in backup_statements:
        obs = RawObservation(id="TEST-BACKUP", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
        result = evaluate_relevance_fallback(obs)
        assert result.relevant is False, f"False positive for backup statement: '{stmt}'"


def test_generic_navigation_and_ui_false_positives():
    """Verify that generic UI, widget, editing, and update complaints remain non-relevant."""
    ui_statements = [
        "The widget has no album option. Major oversight.",
        "Dropped 2 stars just cuz of the disappearance of drag to select feature.",
        "All AI features missing on Razr fold, no eraser etc.",
        "Prompt to update bug keeps popping up every time I open app."
    ]
    for stmt in ui_statements:
        obs = RawObservation(id="TEST-UI", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
        result = evaluate_relevance_fallback(obs)
        assert result.relevant is False, f"False positive for UI/editing statement: '{stmt}'"


def test_genuine_retrieval_failures_true_positives():
    """Verify that genuine photo/video search and retrieval failures are correctly marked relevant."""
    retrieval_statements = [
        "Search is useless - it doesn't come up with anything on first attempt, sometimes never.",
        "Where are my missing album pictures that I uploaded from my Galaxy phone !Still missing!!!",
        "I can't seem to find all my photos.",
        "TEXT/SUBJECT search is FAIL. 'Car Engine' - have 100s of repair photos But Only 15 Show?",
        "The search feature is very inaccurate, and you'll get a migraine before you locate what you're looking for.",
        "Face detection automatically reset I cannot see a familiar face.",
        "The image search feature has actually gotten worse."
    ]
    for stmt in retrieval_statements:
        obs = RawObservation(id="TEST-RETRIEVAL", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
        result = evaluate_relevance_fallback(obs)
        assert result.relevant is True, f"False negative for genuine retrieval statement: '{stmt}'"


def test_grounded_extraction_no_canned_templates():
    """Verify that structured extraction does NOT output static generic canned templates."""
    stmt = "TEXT/SUBJECT search is FAIL. 'Car Engine' - have 100s of repair photos But Only 15 Show?"
    obs = RawObservation(id="TEST-GROUNDED", source="Google Play", url="https://example.com", user_statement=stmt, retrieval_scenario="Not specified")
    
    extracted = extract_observation_fallback(obs)

    # Must NOT contain canned template strings
    assert "Searching for photos using remembered visual concepts or object keywords" not in extracted.retrieval_scenario
    assert "Inability to refine broad search results or concept retrieval gap." not in extracted.failure_point

    # Must be grounded
    assert extracted.problem_category == "Search understanding failure"
    assert "Car Engine" in extracted.search_attempt or "text" in extracted.search_attempt.lower()
    assert extracted.what_user_forgot == "Not mentioned"
    assert extracted.workaround == "Not mentioned"
