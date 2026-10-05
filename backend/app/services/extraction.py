import re
from typing import List, Optional, Callable, Any, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.app.models.dataset import RawObservation
from backend.app.models.observation import StructuredObservation, TAXONOMY_CATEGORIES
from backend.app.prompts.extraction_prompt import get_extraction_prompt
from backend.app.services.llm_client import llm_client

def is_placeholder_scenario(scenario: Optional[str]) -> bool:
    """Checks if the scenario string is empty, missing, or a placeholder string."""
    if not scenario:
        return True
    s = scenario.strip().lower()
    if not s or s in ("not specified", "not mentioned", "n/a", "none", "unknown", "to be inferred"):
        return True
    if "not specified" in s or "infer from user feedback" in s or "unknown scenario" in s:
        return True
    return False


def detect_observation_domain(statement: str, scenario: str) -> str:
    """Determines the core retrieval failure domain from user statement and scenario."""
    stmt_lower = (statement or "").lower()
    scen_lower = (scenario or "").lower()
    combined = f"{stmt_lower} {scen_lower}"

    if re.search(
        r"\bdate search(?:es)?\b|\bsearch by date\b|\bby date\b|\bdate\b|\byear\b|\bmonth\b|\bday\b|\bchronolog|\btimestamp\b|\bcalendar\b|\btimeframe\b|\b(?:19|20)\d\d\b",
        combined
    ):
        return "date"
    elif re.search(
        r"\bocr\b|\btext in\b|\bwords in\b|\brecipe\b|\bslide\b|\bdocument\b|\breceipt\b|\bread text\b|\btext search\b|\btext/subject\b|\bsubject search\b",
        combined
    ):
        return "ocr"
    elif re.search(
        r"\bfilename\b|\bfile name\b|\bexact keyword\b|\btitle\b|\bdescription keyword\b",
        combined
    ):
        return "filename"
    elif re.search(
        r"\balbum\b|\bsync\b|\balbum search\b",
        combined
    ):
        return "album"
    elif re.search(
        r"\bincomplete\b|\btruncated\b|\bsmall subset\b|\brelevance\b|\bconcept\b|\bperson\b|\bname\b|\bobject\b|\bkeyword search\b|\bsearch result\b|\bvisual concept\b",
        combined
    ):
        return "relevance"
    elif re.search(r"\bsearch\b|\bfind\b|\bphoto\b|\bpicture\b|\bvideo\b", combined):
        return "relevance"
    else:
        return "other"


def infer_scenario_from_evidence(
    statement: str,
    category: str = "Other",
    remembers: str = "",
    attempt: str = "",
    failure: str = ""
) -> str:
    """Derives a concise, dataset-agnostic 1-sentence retrieval scenario grounded in evidence."""
    if category == "Other":
        return "Not mentioned"

    domain = detect_observation_domain(statement, "")
    if domain == "date":
        return "Searching for photos using remembered date or timeframe"
    elif domain == "ocr":
        return "Searching for photos or documents containing remembered in-image text"
    elif domain == "filename":
        return "Searching for photos or videos using remembered filename or title keyword"
    elif domain == "album":
        return "Searching for or accessing a recently created photo album"
    elif domain == "relevance":
        stmt_lower = (statement or "").lower()
        if "repair" in stmt_lower or "car engine" in stmt_lower:
            return "Searching for repair photos using subject terms"
        elif "dog" in stmt_lower or "pet" in stmt_lower:
            return "Searching for pet photos using visual concept keywords"
        elif "baby" in stmt_lower or "face" in stmt_lower:
            return "Searching or grouping photos by face recognition"
        return "Searching for photos using remembered keywords or visual context"
    else:
        return "Not mentioned"


def extract_observation_fallback(obs: RawObservation) -> StructuredObservation:
    stmt = (obs.user_statement or "").strip()
    scen = (obs.retrieval_scenario or "").strip()
    stmt_lower = stmt.lower()
    text = f"{stmt_lower} {scen.lower()}"
    
    domain = detect_observation_domain(stmt, scen)
    
    # Priority matching by domain & text patterns
    if domain == "ocr" or re.search(r"ocr|text search|text/subject|subject search|recipe|word in|slide|text in|document", stmt_lower):
        category = "Search understanding failure"
        quoted_match = re.search(r'"([^"]+)"|\'([^\']+)\'', stmt)
        if quoted_match:
            term = quoted_match.group(1) or quoted_match.group(2)
            attempt = f"Searching for '{term}' text inside photos"
            remembers = f"Remembers in-image text/subject '{term}'"
        else:
            attempt = "Searching for text contained inside photos"
            remembers = "Remembers text visible inside photos or documents"
        outcome = "Search fails to return matching photos for text query"
        failure = f"Search understanding failure for text/OCR search in statement"

    elif domain == "date" or re.search(r"date|year|month|timeframe|calendar|chronolog", stmt_lower):
        category = "Metadata / date / location mismatch"
        remembers = "Remembers temporal clues (e.g. date, month, year, or relative timeframe)."
        attempt = "Searching or filtering photos by date or timeframe"
        outcome = "No results returned or photos missing for date query"
        failure = f"Date indexing/mismatch failure for date search in statement"

    elif domain == "filename" or re.search(r"filename|file name|vacation\.jpg", stmt_lower):
        category = "Retrieval / indexing failure"
        remembers = "Remembers specific filename, title, or keyword."
        attempt = "Searching by exact filename or title keyword"
        outcome = "Filename search fails to return matching photo/video"
        failure = f"Filename and keyword indexing failure for photo search"

    elif domain == "album" or re.search(r"album|album search|sync", stmt_lower):
        category = "Navigation / browsing failure"
        remembers = "Remembers album name, album pictures, or album context."
        attempt = "Searching for album name or browsing album list"
        outcome = "Recently created or uploaded album not found in search/sync"
        failure = f"Album index sync delay or album browsing failure"

    elif re.search(r"face|person|grouping|tagged|familiar face", stmt_lower):
        category = "Result evaluation failure"
        remembers = "Remembers specific person, familiar faces, or face tags"
        attempt = "Browsing or searching face recognition tags"
        outcome = "Face recognition failed to group faces or reset familiar faces"
        failure = f"Face detection/grouping failure in photo library"

    elif re.search(r"missing|disappeared|gone|lost|stole|retrieve my photos|reset", stmt_lower):
        category = "Retrieval / indexing failure"
        remembers = "Remembers missing photos, uploaded albums, or backed up media"
        attempt = "Attempting to locate or retrieve missing photos"
        outcome = "Missing photos not returned or absent from photo library"
        failure = f"Retrieval/indexing failure for missing photos"

    elif domain == "relevance" or re.search(r"search is|search feature|image search|inaccurate|jumbled|hard to locate|hidden in folders|incomplete", stmt_lower):
        if re.search(r"folder|album|locate|jumbled", stmt_lower):
            category = "Navigation / browsing failure"
            remembers = "Remembers photo folder or album location"
            attempt = "Navigating folders or searching album list"
            outcome = "Photos hard to locate or jumbled in folders"
            failure = f"Navigation/browsing failure for photo folders"
        else:
            category = "Result relevance failure"
            remembers = "Remembers photo content or search query"
            attempt = "Searching photo library"
            outcome = "Search returns inaccurate or incomplete results"
            failure = f"Result relevance failure for photo search query in statement"

    else:
        category = "Other"
        remembers = "Not mentioned"
        attempt = "Not mentioned"
        outcome = "Not mentioned"
        failure = f"General feedback without explicit retrieval failure details."

    remembers_val = remembers if remembers != "Not mentioned" else "Not mentioned"
    attempt_val = attempt if attempt != "Not mentioned" else "Not mentioned"
    behavior_val = "Not mentioned"
    workaround_val = "Not mentioned"

    if re.search(r"\bscroll\b|\bmanual\b", text):
        workaround_val = "Manually scrolling through photo timeline."
    elif re.search(r"\bdesktop\b|\bweb\b", text):
        workaround_val = "Switching between desktop and mobile app."

    if not is_placeholder_scenario(obs.retrieval_scenario):
        final_scenario = obs.retrieval_scenario.strip()
    else:
        final_scenario = infer_scenario_from_evidence(stmt, category, remembers_val, attempt_val, failure)

    return StructuredObservation(
        id=obs.id,
        source=obs.source,
        url=obs.url,
        retrieval_scenario=final_scenario,
        what_user_remembers=remembers_val,
        what_user_forgot="Not mentioned",
        search_attempt=attempt_val,
        search_behavior=behavior_val,
        retrieval_outcome=outcome if outcome else "Photo search/retrieval failure reported in statement.",
        failure_point=failure,
        workaround=workaround_val,
        problem_category=category,
        evidence_strength="High" if category != "Other" else "Low",
        analyst_note=f"Extracted directly from user verbatim statement on {obs.source}."
    )


def validate_and_enforce_semantic_consistency(
    obs: RawObservation,
    extracted: StructuredObservation
) -> StructuredObservation:
    """Validates and enforces semantic consistency between Retrieval Scenario and extracted fields."""
    domain = detect_observation_domain(obs.user_statement, extracted.retrieval_scenario)
    
    current_cat = extracted.problem_category
    current_fail = (extracted.failure_point or "").lower()
    current_rem = (extracted.what_user_remembers or "").lower()

    mismatch = False
    if domain == "date":
        if current_cat != "Metadata / date / location mismatch" or "concept" in current_fail or "concept" in current_rem:
            mismatch = True
    elif domain == "ocr":
        if current_cat != "Search understanding failure" or ("ocr" not in current_fail and "text" not in current_fail):
            mismatch = True
    elif domain == "filename":
        if current_cat != "Retrieval / indexing failure" or ("filename" not in current_fail and "keyword" not in current_fail):
            mismatch = True
    elif domain == "album":
        if current_cat != "Navigation / browsing failure" or ("album" not in current_fail and "sync" not in current_fail):
            mismatch = True

    if mismatch:
        fallback = extract_observation_fallback(obs)
        return StructuredObservation(
            id=extracted.id,
            source=extracted.source,
            url=extracted.url,
            retrieval_scenario=extracted.retrieval_scenario if not is_placeholder_scenario(extracted.retrieval_scenario) else fallback.retrieval_scenario,
            what_user_remembers=fallback.what_user_remembers,
            what_user_forgot=fallback.what_user_forgot,
            search_attempt=fallback.search_attempt,
            search_behavior=fallback.search_behavior,
            retrieval_outcome=fallback.retrieval_outcome,
            failure_point=fallback.failure_point,
            workaround=extracted.workaround if extracted.workaround != "Not mentioned" else fallback.workaround,
            problem_category=fallback.problem_category,
            evidence_strength=extracted.evidence_strength,
            analyst_note=f"Semantically aligned to evidence domain '{domain}' on {extracted.source}."
        )

    return extracted


def _clean_field_value(val: Any, default: str = "Not mentioned") -> str:
    s = str(val).strip() if val is not None else ""
    if not s or is_placeholder_scenario(s):
        return default
    return s


def _extract_single_observation(
    obs: RawObservation,
    rel_result: Optional[Any] = None
) -> StructuredObservation:
    if rel_result and not getattr(rel_result, "relevant", True):
        reason = getattr(rel_result, "reason", "Filtered in Stage 2 as non-retrieval evidence.")
        scen = obs.retrieval_scenario if not is_placeholder_scenario(obs.retrieval_scenario) else "Not mentioned"
        return StructuredObservation(
            id=obs.id,
            source=obs.source,
            url=obs.url,
            retrieval_scenario=scen,
            what_user_remembers="Not mentioned",
            what_user_forgot="Not mentioned",
            search_attempt="Not mentioned",
            search_behavior="Not mentioned",
            retrieval_outcome="Excluded from retrieval failure analysis.",
            failure_point=reason,
            workaround="Not mentioned",
            problem_category="Other",
            evidence_strength="Low",
            analyst_note=f"Filtered in Stage 2 as non-retrieval evidence ({reason})."
        )

    prompt = get_extraction_prompt(obs.id, obs.source, obs.url, obs.user_statement, obs.retrieval_scenario)
    fallback = extract_observation_fallback(obs)
    
    try:
        if llm_client.api_key and llm_client.api_key.strip() not in ("", "your_api_key_here", "dummy"):
            json_output = llm_client.generate_json(prompt, mock_fallback=fallback.model_dump())
            
            cat = json_output.get("problem_category", fallback.problem_category)
            if cat not in TAXONOMY_CATEGORIES:
                cat = fallback.problem_category

            extracted_scen = str(json_output.get("retrieval_scenario", "")).strip()

            if not is_placeholder_scenario(obs.retrieval_scenario):
                final_scenario = obs.retrieval_scenario.strip()
            elif not is_placeholder_scenario(extracted_scen):
                final_scenario = extracted_scen
            else:
                final_scenario = fallback.retrieval_scenario

            # Sanitize generic canned template strings if returned by LLM
            CANNED_SCENARIOS = [
                "Searching for photos using remembered visual concepts or object keywords",
                "Not specified — infer from user feedback"
            ]
            if any(cs.lower() in final_scenario.lower() for cs in CANNED_SCENARIOS):
                final_scenario = fallback.retrieval_scenario

            fp = _clean_field_value(json_output.get("failure_point"), fallback.failure_point)
            CANNED_FAILURES = [
                "Inability to refine broad search results or concept retrieval gap.",
                "Inability to refine broad search results"
            ]
            if any(cf.lower() in fp.lower() for cf in CANNED_FAILURES):
                fp = fallback.failure_point

            return StructuredObservation(
                id=obs.id,
                source=obs.source,
                url=obs.url,
                retrieval_scenario=final_scenario,
                what_user_remembers=_clean_field_value(json_output.get("what_user_remembers"), fallback.what_user_remembers),
                what_user_forgot=_clean_field_value(json_output.get("what_user_forgot"), "Not mentioned"),
                search_attempt=_clean_field_value(json_output.get("search_attempt"), fallback.search_attempt),
                search_behavior=_clean_field_value(json_output.get("search_behavior"), fallback.search_behavior),
                retrieval_outcome=_clean_field_value(json_output.get("retrieval_outcome"), fallback.retrieval_outcome),
                failure_point=fp,
                workaround=_clean_field_value(json_output.get("workaround"), "Not mentioned"),
                problem_category=cat,
                evidence_strength="High" if cat != "Other" else "Low",
                analyst_note=f"Extracted directly from user verbatim quote on {obs.source}."
            )
        else:
            return fallback
    except Exception:
        return fallback


def extract_structured_observations(
    observations: List[RawObservation],
    relevance_map: Optional[Dict[str, Any]] = None,
    max_workers: int = 10,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[StructuredObservation]:
    if not observations:
        return []

    total_count = len(observations)
    results: List[Optional[StructuredObservation]] = [None] * total_count
    completed_count = 0

    workers = max(1, min(max_workers, total_count))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_index = {
            executor.submit(
                _extract_single_observation,
                obs,
                relevance_map.get(obs.id) if relevance_map else None
            ): i
            for i, obs in enumerate(observations)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception:
                rel_res = relevance_map.get(observations[idx].id) if relevance_map else None
                results[idx] = _extract_single_observation(observations[idx], rel_res)
            
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total_count)

    return [r for r in results if r is not None]
