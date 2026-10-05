import re
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.app.models.dataset import RawObservation
from backend.app.models.analysis import RelevanceResult
from backend.app.prompts.relevance_prompt import get_relevance_prompt
from backend.app.services.llm_client import llm_client

# Positive praise without retrieval failure
POSITIVE_PRAISE_PATTERNS = [
    r"\bgood\b", r"\bnice\b", r"\bbest app\b", r"\bawesome\b", r"\blove this app\b",
    r"\beffortless\b", r"\btop-tier\b", r"\bfantastic\b", r"\beasy backup\b", r"\bnice interface\b",
    r"\bgreat app\b", r"\blove google photos\b", r"\buseful\b", r"\bvery good\b", r"\bexcelent\b",
    r"\bexcellent\b", r"\bhandy\b", r"\bconvenient\b", r"\bperfect\b", r"\bwonderful\b", r"\bthe best\b"
]

# Non-retrieval domain exclusions
NON_RETRIEVAL_DOMAINS = [
    (r"\bshare\b|\bsharing\b|\bpartner sharing\b|\bsend photo\b|\bsending\b", "sharing"),
    (r"\bstorage\b|\bgoogle one\b|\bquota\b|\bsubscription\b|\bpay\b|\b15gb\b|\bspace\b|\bbuy storage\b|\bcost\b|\bprice\b", "storage & pricing"),
    (r"\bback\s?up\b|\bbacking up\b|\bsync\b|\bsyncing\b", "backup & sync"),
    (r"\bedit\b|\bediting\b|\bfilter\b|\bfilters\b|\bunblur\b|\beraser\b|\bcrop\b|\bmagic eraser\b|\bmusic\b|\bretouch\b", "photo editing & filters"),
    (r"\bdownload\b|\bdownloading\b|\bexport\b|\bexporting\b", "download & export"),
    (r"\baccount\b|\blogin\b|\bpassword\b|\bpermission\b|\bsign in\b", "account & security"),
    (r"\bupdate\b|\bupdates\b|\bwidget\b|\bbattery\b|\bcrash\b|\blayout\b|\bicon\b|\bsd card\b|\bdrag to select\b|\bsave copy\b", "generic UI, app update & performance"),
    (r"\bcamera\b|\bshutter\b", "camera app")
]

# Explicit retrieval failure & intent regex patterns
RETRIEVAL_FAILURE_PATTERNS = [
    r"can'?t find", r"cannot find", r"couldn'?t find", r"unable to find", r"hard to find", r"trouble finding", r"failed to find",
    r"where (?:is|are) my", r"missing (?:from|in) search", r"not (?:appearing|showing) in search", r"pictures? (?:is|are) missing",
    r"no result", r"zero result", r"no longer return", r"no longer returns", r"nothing (?:showed|came|turned) up", r"wrong (?:photo|photos|picture|pictures|result|results)",
    r"search (?:is|doesn'?t|fails|not|broken|useless|horrible|terrible|slow|sucks|inaccurate|worse|gotten worse)",
    r"date search", r"date-based search", r"search by date", r"face (?:detection|grouping|search|recognition)", r"ocr search", r"text search", r"album search",
    r"can'?t search", r"retrieve my photos", r"retrieve older", r"retrieving older", r"search returns", r"find all my photos", r"misfiled", r"hard to locate", r"hidden in folders",
    r"search feature", r"text/subject search", r"image search", r"find my", r"locate my",
    r"search result", r"incomplete", r"retrieving visual concept", r"visual concept",
    r"searched for", r"searched by", r"searching for", r"searching by", r"filename"
]


def evaluate_relevance_fallback(obs: RawObservation) -> RelevanceResult:
    stmt = (obs.user_statement or "").strip()
    scen = (obs.retrieval_scenario or "").strip()
    stmt_lower = stmt.lower()
    full_lower = f"{stmt_lower} {scen.lower()}"

    # Check for explicit photo retrieval failure evidence
    has_retrieval_failure = any(re.search(p, full_lower) for p in RETRIEVAL_FAILURE_PATTERNS)

    # Check for complaint keywords
    has_complaint = any(re.search(p, stmt_lower) for p in [
        r"\bfail", r"\bproblem", r"\bcannot", r"\bcan'?t", r"\bno result", r"\bmissing",
        r"\bbroken", r"\bdifficult", r"\bhard to", r"\bhorrible", r"\binaccurate",
        r"\buseless", r"\bgone", r"\blost", r"\bworse", r"\bglitch", r"\bincomplete",
        r"\bnothing showed", r"\bnothing came", r"\bno longer return"
    ])

    # Check if observation is positive praise without retrieval failure
    is_praise = any(re.search(p, stmt_lower) for p in POSITIVE_PRAISE_PATTERNS) and not (has_retrieval_failure or has_complaint)

    if is_praise:
        return RelevanceResult(
            id=obs.id,
            relevant=False,
            reason="Positive review without reporting a photo retrieval problem."
        )

    # Non-retrieval domain match
    if not has_retrieval_failure:
        for pat, dom in NON_RETRIEVAL_DOMAINS:
            if re.search(pat, stmt_lower):
                return RelevanceResult(
                    id=obs.id,
                    relevant=False,
                    reason=f"Describes {dom} issue without photo/video retrieval problem."
                )

    if has_retrieval_failure:
        return RelevanceResult(
            id=obs.id,
            relevant=True,
            reason="Explicit evidence of photo/video retrieval failure or friction."
        )

    return RelevanceResult(
        id=obs.id,
        relevant=False,
        reason="Lacks explicit evidence of photo/video search or retrieval scenario."
    )


def _evaluate_single_relevance(obs: RawObservation) -> RelevanceResult:
    prompt = get_relevance_prompt(obs.id, obs.user_statement, obs.retrieval_scenario)
    fallback = evaluate_relevance_fallback(obs)
    
    try:
        if llm_client.api_key and llm_client.api_key.strip() not in ("", "your_api_key_here", "dummy"):
            json_output = llm_client.generate_json(prompt, mock_fallback=fallback.model_dump())
            llm_relevant = bool(json_output.get("relevant", False))
            
            # Strict enforcement: if fallback rejected as praise, non-retrieval domain, or lack of retrieval failure, enforce rejection
            if not fallback.relevant:
                return fallback
                
            return RelevanceResult(
                id=obs.id,
                relevant=llm_relevant,
                reason=str(json_output.get("reason", fallback.reason))
            )
        else:
            return fallback
    except Exception:
        return fallback


def filter_relevance(
    observations: List[RawObservation],
    max_workers: int = 10,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[RelevanceResult]:
    if not observations:
        return []

    total_count = len(observations)
    results: List[Optional[RelevanceResult]] = [None] * total_count
    completed_count = 0

    workers = max(1, min(max_workers, total_count))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_index = {
            executor.submit(_evaluate_single_relevance, obs): i
            for i, obs in enumerate(observations)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = evaluate_relevance_fallback(observations[idx])
            
            completed_count += 1
            if progress_callback:
                progress_callback(completed_count, total_count)

    return [r for r in results if r is not None]
