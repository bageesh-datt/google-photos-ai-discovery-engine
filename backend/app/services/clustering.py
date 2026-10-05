import re
import json
from typing import List, Any
from backend.app.models.observation import StructuredObservation
from backend.app.models.cluster import ProblemCluster
from backend.app.prompts.clustering_prompt import get_clustering_prompt
from backend.app.services.llm_client import llm_client

def is_valid_retrieval_observation(o: Any) -> bool:
    """
    Dataset-agnostic evidence eligibility filter:
    Only observations with valid, strong photo/video retrieval failure evidence
    are eligible to form recurring problem clusters and research opportunities.
    Weak/ambiguous observations (category "Other", evidence_strength "Low", or general feedback)
    remain in the observation layer for audit transparency but are excluded from cluster evidence.
    """
    if isinstance(o, dict):
        cat = o.get("problem_category", "")
        strength = o.get("evidence_strength", "")
        failure = str(o.get("failure_point", ""))
    else:
        cat = getattr(o, "problem_category", "")
        strength = getattr(o, "evidence_strength", "")
        failure = str(getattr(o, "failure_point", ""))

    if cat == "Other":
        return False
    if strength == "Low":
        return False
    if "General feedback without explicit retrieval failure details" in failure:
        return False

    return True


def cluster_observations_fallback(observations: List[StructuredObservation]) -> List[ProblemCluster]:
    # Filter observations by explicit category and word boundary matching
    date_ids = [
        o.id for o in observations
        if o.problem_category == "Metadata / date / location mismatch" or
        re.search(r"\bdate\b|\byear\b|\bmonth\b|\bchronolog", f"{o.what_user_remembers} {o.retrieval_scenario}".lower())
    ]
    
    text_ids = [
        o.id for o in observations
        if (o.problem_category == "Search understanding failure" and re.search(r"\bocr\b|\btext\b|\bword\b|\brecipe\b|\bdocument\b", f"{o.what_user_remembers} {o.retrieval_scenario}".lower())) or
        re.search(r"\bocr\b|\btext in\b", f"{o.what_user_remembers} {o.retrieval_scenario}".lower())
    ]
    
    nav_ids = [
        o.id for o in observations
        if o.problem_category == "Navigation / browsing failure" or
        re.search(r"\balbum\b|\bsync\b", f"{o.what_user_remembers} {o.retrieval_scenario}".lower())
    ]
    
    indexing_ids = [
        o.id for o in observations
        if o.id not in date_ids and o.id not in text_ids and o.id not in nav_ids and o.problem_category != "Other"
    ]

    clusters: List[ProblemCluster] = []
    
    if date_ids:
        clusters.append(ProblemCluster(
            cluster_id=f"CL-{len(clusters)+1:02d}",
            cluster_name="Date-Based Retrieval & Indexing Failures",
            core_problem="Users remember approximate months, years, or relative timeframes, but exact date search queries fail to return matching photos.",
            supporting_observation_ids=date_ids,
            count=len(date_ids),
            what_users_remember="Approximate year, month, or relative holiday timeframe.",
            what_is_missing="Exact day or timestamp metadata.",
            typical_search_behavior="Entering month/year queries or changing date formats.",
            failure_point="Date search returns zero results or irrelevant older photos.",
            workarounds="Manual timeline scrolling or switching between desktop and mobile devices.",
            evidence_summary=f"Supported by {len(date_ids)} public user observations ({', '.join(date_ids)}).",
            open_questions_for_interviews=[
                "When searching for a photo from years ago, how do you express the time range in your mind?",
                "What happens when you search by year or month and get no results?",
                "How long do you scroll manually before giving up on a date-based search?"
            ]
        ))

    if text_ids:
        clusters.append(ProblemCluster(
            cluster_id=f"CL-{len(clusters)+1:02d}",
            cluster_name="Text/OCR Content Retrieval Failures",
            core_problem="Users attempt to retrieve documents, recipes, or slides using remembered text appearing inside the image, but text search fails to surface matching items.",
            supporting_observation_ids=text_ids,
            count=len(text_ids),
            what_users_remember="Words, handwritten notes, slide headers, or document text visible in image.",
            what_is_missing="Exact file title or upload timestamp.",
            typical_search_behavior="Searching for exact words contained inside the document or photo.",
            failure_point="Optical Character Recognition (OCR) indexing fails to surface image.",
            workarounds="Browsing document/screenshot albums manually.",
            evidence_summary=f"Supported by {len(text_ids)} public user observations ({', '.join(text_ids)}).",
            open_questions_for_interviews=[
                "How often do you rely on text inside a photo (recipes, receipts, slides) to find it later?",
                "What specific text keywords do you try first when looking for a document photo?",
                "How do you distinguish high-value receipts/documents from routine screenshots?"
            ]
        ))

    if indexing_ids:
        clusters.append(ProblemCluster(
            cluster_id=f"CL-{len(clusters)+1:02d}",
            cluster_name="Result Relevance & Breadth Failures",
            core_problem="Users search using remembered visual concepts, filenames, or person names, but search returns empty results or small unrefined subsets.",
            supporting_observation_ids=indexing_ids,
            count=len(indexing_ids),
            what_users_remember="Visual concepts (objects, familiar activities, person names, filenames).",
            what_is_missing="Exact metadata tags or full contextual description.",
            typical_search_behavior="Searching by generic object keywords or person names.",
            failure_point="Semantic indexing fails or returns incomplete photo subsets.",
            workarounds="Retrying broad queries or giving up search entirely.",
            evidence_summary=f"Supported by {len(indexing_ids)} public user observations ({', '.join(indexing_ids)}).",
            open_questions_for_interviews=[
                "What visual details or concepts do you usually remember when trying to find a photo?",
                "How do you refine a broad concept search when too many or too few results appear?",
                "What do you expect Google Photos to understand when you describe a photo using visual concepts?"
            ]
        ))

    if nav_ids:
        clusters.append(ProblemCluster(
            cluster_id=f"CL-{len(clusters)+1:02d}",
            cluster_name="Navigation / Album Sync Delays",
            core_problem="Users expect newly created albums to become searchable immediately, but indexing and sync delays prevent created albums from appearing in search queries.",
            supporting_observation_ids=nav_ids,
            count=len(nav_ids),
            what_users_remember="Newly created album title or recent creation timestamp.",
            what_is_missing="Immediate search index sync status.",
            typical_search_behavior="Searching for newly created album by title in search bar.",
            failure_point="Album sync/indexing delay between creation and search availability.",
            workarounds="Waiting, refreshing repeatedly, or manually scrolling through album list.",
            evidence_summary=f"Supported by {len(nav_ids)} public user observations ({', '.join(nav_ids)}).",
            open_questions_for_interviews=[
                "How quickly do you expect a newly created album to appear in search?",
                "How often do you retry search when the album is not immediately available?",
                "Do you understand that indexing or sync may be delayed?"
            ]
        ))
        
    return clusters


def validate_and_repair_cluster_coverage(
    observations: List[StructuredObservation],
    clusters: List[ProblemCluster]
) -> List[ProblemCluster]:
    if not observations:
        return clusters

    all_input_ids = [o.id for o in observations if is_valid_retrieval_observation(o)]
    obs_map = {o.id: o for o in observations if is_valid_retrieval_observation(o)}
    
    covered_ids = set()
    for c in clusters:
        covered_ids.update(c.supporting_observation_ids)
        
    missing_ids = [oid for oid in all_input_ids if oid not in covered_ids]
    if not missing_ids:
        return clusters

    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by",
        "is", "was", "are", "were", "be", "user", "users", "photo", "photos", "search",
        "searches", "trying", "retrieve", "retrieval", "using", "when", "that", "this", "from"
    }

    def get_tokens(text: str) -> set:
        raw_words = text.lower().replace("/", " ").replace("-", " ").replace(".", " ").split()
        return {w for w in raw_words if w not in stop_words and len(w) > 2}

    domain_keywords = {
        "date": ["date", "time", "year", "month", "july", "day", "prior", "chronological", "timestamp", "calendar", "temporal"],
        "text": ["text", "ocr", "word", "document", "recipe", "slide", "read", "handwritten", "receipt"],
        "nav": ["album", "sync", "navigation", "delay", "recent", "created"],
        "relevance": ["relevance", "breadth", "keyword", "filename", "concept", "subset", "broad", "result", "search understanding", "missing", "incomplete", "find", "classic"]
    }

    repaired_clusters = [c for c in clusters]

    for missing_id in missing_ids:
        obs = obs_map[missing_id]
        obs_text = f"{obs.problem_category} {obs.retrieval_scenario} {obs.what_user_remembers} {obs.failure_point} {getattr(obs, 'user_statement', '')}".lower()
        obs_tokens = get_tokens(obs_text)

        obs_domains = set()
        for domain, kw_list in domain_keywords.items():
            if any(kw in obs_text for kw in kw_list):
                obs_domains.add(domain)

        best_cluster = None
        best_score = -1.0

        for cluster in repaired_clusters:
            cluster_text = f"{cluster.cluster_name} {cluster.core_problem} {cluster.failure_point} {cluster.typical_search_behavior} {cluster.evidence_summary}".lower()
            cluster_tokens = get_tokens(cluster_text)

            cluster_domains = set()
            for domain, kw_list in domain_keywords.items():
                if any(kw in cluster_text for kw in kw_list):
                    cluster_domains.add(domain)

            domain_score = len(obs_domains.intersection(cluster_domains)) * 10.0
            token_score = len(obs_tokens.intersection(cluster_tokens)) * 1.0
            total_score = domain_score + token_score

            if total_score > best_score:
                best_score = total_score
                best_cluster = cluster

        if best_cluster is not None and best_score > 0:
            if missing_id not in best_cluster.supporting_observation_ids:
                best_cluster.supporting_observation_ids.append(missing_id)
                best_cluster.count = len(best_cluster.supporting_observation_ids)
        else:
            new_cl_id = f"CL-{len(repaired_clusters)+1:02d}"
            new_cluster = ProblemCluster(
                cluster_id=new_cl_id,
                cluster_name="Result Relevance & Breadth Failures",
                core_problem="Keyword or visual concept searches return missing, unrefined, or incomplete photo subsets.",
                supporting_observation_ids=[missing_id],
                count=1,
                what_users_remember=obs.what_user_remembers or "Remembered visual details or filenames.",
                what_is_missing=obs.what_user_forgot or "Exact metadata tags.",
                typical_search_behavior="Keyword or concept search.",
                failure_point=obs.failure_point or "Search understanding breakdown.",
                workarounds="Retrying queries or browsing manually.",
                evidence_summary=f"Supported by 1 public user observation ({missing_id}).",
                open_questions_for_interviews=[
                    "How do you refine keyword searches when matching photos do not appear?",
                    "What visual details or concepts do you usually remember when trying to find a photo?"
                ]
            )
            repaired_clusters.append(new_cluster)

    for c in repaired_clusters:
        c.count = len(c.supporting_observation_ids)
        c.evidence_summary = f"Supported by {c.count} public user observation(s) ({', '.join(c.supporting_observation_ids)})."

    return repaired_clusters


def cluster_observations(observations: List[StructuredObservation]) -> List[ProblemCluster]:
    if not observations:
        return []
        
    # Dataset-agnostic filtering: only valid, strong retrieval observations form clusters
    eligible_obs = [o for o in observations if is_valid_retrieval_observation(o)]
    if not eligible_obs:
        return []

    fallback = cluster_observations_fallback(eligible_obs)
    
    if not llm_client.api_key or llm_client.api_key.strip() in ("", "your_api_key_here", "dummy"):
        return validate_and_repair_cluster_coverage(eligible_obs, fallback)
        
    obs_summary = [
        {
            "id": o.id,
            "retrieval_scenario": o.retrieval_scenario,
            "what_user_remembers": o.what_user_remembers,
            "what_user_forgot": o.what_user_forgot,
            "failure_point": o.failure_point,
            "problem_category": o.problem_category
        }
        for o in eligible_obs
    ]
    prompt = get_clustering_prompt(json.dumps(obs_summary, indent=2))
    
    try:
        json_output = llm_client.generate_json(prompt, mock_fallback=[c.model_dump() for c in fallback])
        if isinstance(json_output, list):
            valid_clusters = []
            eligible_ids = set(o.id for o in eligible_obs)
            for item in json_output:
                supp_ids = [oid for oid in item.get("supporting_observation_ids", []) if oid in eligible_ids]
                if supp_ids:
                    valid_clusters.append(ProblemCluster(
                        cluster_id=str(item.get("cluster_id", f"CL-{len(valid_clusters)+1:02d}")),
                        cluster_name=str(item.get("cluster_name", "Recurring Retrieval Issue")),
                        core_problem=str(item.get("core_problem", "User retrieval friction")),
                        supporting_observation_ids=supp_ids,
                        count=len(supp_ids),
                        what_users_remember=str(item.get("what_users_remember", "Vague memory clues")),
                        what_is_missing=str(item.get("what_is_missing", "Missing timestamp/metadata")),
                        typical_search_behavior=str(item.get("typical_search_behavior", "Search attempt")),
                        failure_point=str(item.get("failure_point", "Search breakdown")),
                        workarounds=str(item.get("workarounds", "Not mentioned")),
                        evidence_summary=f"Supported by {len(supp_ids)} public user observation(s) ({', '.join(supp_ids)}).",
                        open_questions_for_interviews=list(item.get("open_questions_for_interviews", []))
                    ))
            result = valid_clusters if valid_clusters else fallback
            return validate_and_repair_cluster_coverage(eligible_obs, result)
        return validate_and_repair_cluster_coverage(eligible_obs, fallback)
    except Exception:
        return validate_and_repair_cluster_coverage(eligible_obs, fallback)
