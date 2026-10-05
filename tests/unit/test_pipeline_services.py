import pytest
from backend.app.models.dataset import RawObservation
from backend.app.models.observation import TAXONOMY_CATEGORIES
from backend.app.services.relevance import filter_relevance
from backend.app.services.extraction import extract_structured_observations
from backend.app.services.clustering import cluster_observations
from backend.app.services.opportunities import synthesize_opportunities
from backend.app.services.llm_client import llm_client

@pytest.fixture(autouse=True)
def disable_llm_api_key(monkeypatch):
    monkeypatch.setattr(llm_client, "api_key", "")

@pytest.fixture
def sample_raw_observations():
    return [
        RawObservation(
            id="R01",
            source="Reddit",
            url="https://www.reddit.com/r/googlephotos/comments/1v3gsds/",
            user_statement="The user says date-based searches that previously worked, such as July 2016, no longer return results.",
            retrieval_scenario="Trying to retrieve older family photos using a remembered month/year."
        ),
        RawObservation(
            id="R02",
            source="Reddit",
            url="https://www.reddit.com/r/googlephotos/comments/1ijy6ie/",
            user_statement="The user says text-search across images stopped finding many images even when the text is clearly recognizable.",
            retrieval_scenario="Trying to retrieve a document or image by remembered text appearing inside the image."
        ),
        RawObservation(
            id="GP01",
            source="PlayStore",
            url="https://play.google.com/store/apps/details?id=com.google.android.apps.photos",
            user_statement="App keeps asking me to buy Google One storage quota every time I open it!",
            retrieval_scenario="Storage quota complaint"
        )
    ]


def test_relevance_filtering(sample_raw_observations):
    relevance_results = filter_relevance(sample_raw_observations)
    assert len(relevance_results) == 3
    
    r01_result = next(r for r in relevance_results if r.id == "R01")
    assert r01_result.relevant is True
    
    gp01_result = next(r for r in relevance_results if r.id == "GP01")
    assert gp01_result.relevant is False


def test_relevance_filtering_strict_inclusion_and_noise_rejection():
    test_cases = [
        # FALSE Cases
        ("F01", "good", "Generic praise", False),
        ("F02", "nice", "Generic review", False),
        ("F03", "very good and beautiful", "Generic rating", False),
        ("F04", "update nahi ho raha hai", "App update complaint without search context", False),
        ("F05", "constant nagging to use their back up service gets old", "Backup complaint without search context", False),
        ("F06", "lines now appear across every picture when using unblur feature", "Editing/filter complaint", False),
        ("F07", "Uses mobile data can't view pictures if you don't have data", "Data usage complaint without search context", False),
        ("F08", "Serves as a top-tier digital archive making image retrieval effortless", "Positive statement saying retrieval works well", False),
        ("F09", "some people do without permission I'm not a casting", "Vague statement with no retrieval evidence", False),
        ("F10", "my google account find out", "Account access complaint without photo retrieval context", False),
        
        # TRUE Cases
        ("T01", "I can't find my old photos", "Photo search problem", True),
        ("T02", "I searched by date but got no results", "Date search problem", True),
        ("T03", "I can't find the document using the text in the photo", "OCR text search issue", True),
        ("T04", "search results are incomplete", "Result completeness issue", True),
        ("T05", "I remember the photo was from 2019 but search doesn't show it", "Date memory retrieval gap", True),
        ("T06", "I created an album but can't find the photos when searching", "Album search sync issue", True),
    ]

    raw_obs_list = [
        RawObservation(
            id=id_,
            source="Test",
            url="http://example.com",
            user_statement=stmt,
            retrieval_scenario=scen
        )
        for id_, stmt, scen, _ in test_cases
    ]

    results = filter_relevance(raw_obs_list)
    res_map = {r.id: r.relevant for r in results}

    for id_, stmt, scen, expected in test_cases:
        assert res_map[id_] is expected, f"Failed for statement '{stmt}': expected {expected}, got {res_map[id_]}"



def test_structured_observation_extraction(sample_raw_observations):
    relevant_obs = [o for o in sample_raw_observations if o.id in ("R01", "R02")]
    extracted = extract_structured_observations(relevant_obs)
    
    assert len(extracted) == 2
    r01_obs = extracted[0]
    
    # Check 14 fields presence
    assert r01_obs.id == "R01"
    assert r01_obs.source == "Reddit"
    assert r01_obs.url == "https://www.reddit.com/r/googlephotos/comments/1v3gsds/"
    assert r01_obs.retrieval_scenario == "Trying to retrieve older family photos using a remembered month/year."
    assert r01_obs.problem_category in TAXONOMY_CATEGORIES
    assert r01_obs.evidence_strength in ("High", "Medium", "Low")
    assert len(r01_obs.what_user_remembers) > 0
    assert len(r01_obs.failure_point) > 0


def test_clustering_preserves_supporting_observation_ids(sample_raw_observations):
    relevant_obs = [o for o in sample_raw_observations if o.id in ("R01", "R02")]
    extracted = extract_structured_observations(relevant_obs)
    clusters = cluster_observations(extracted)
    
    assert len(clusters) > 0
    for cluster in clusters:
        assert len(cluster.supporting_observation_ids) > 0
        assert cluster.count == len(cluster.supporting_observation_ids)
        # Verify IDs exist in extracted set
        for obs_id in cluster.supporting_observation_ids:
            assert obs_id in ("R01", "R02")


def test_opportunity_synthesis_traceability(sample_raw_observations):
    relevant_obs = [o for o in sample_raw_observations if o.id in ("R01", "R02")]
    extracted = extract_structured_observations(relevant_obs)
    clusters = cluster_observations(extracted)
    opportunities = synthesize_opportunities(clusters)
    
    assert len(opportunities) > 0
    for opp in opportunities:
        assert len(opp.supporting_evidence_ids) > 0
        # Verify no product features or UI recommendations in titles
        name_lower = opp.opportunity_name.lower()
        assert "button" not in name_lower
        assert "build a chat" not in name_lower
        assert "app feature" not in name_lower


def test_opportunity_synthesis_distinct_clusters_and_album_navigation_fix():
    from backend.app.models.cluster import ProblemCluster
    clusters = [
        ProblemCluster(
            cluster_id="CL-01",
            cluster_name="Date-Based Retrieval & Indexing Failures",
            core_problem="Date index failures",
            supporting_observation_ids=["R01", "GS01"],
            count=2,
            what_users_remember="Month/year",
            what_is_missing="Exact day",
            typical_search_behavior="Date query",
            failure_point="Zero results",
            workarounds="Manual scroll",
            evidence_summary="Supported by 2 observations",
            open_questions_for_interviews=["Validation question"]
        ),
        ProblemCluster(
            cluster_id="CL-02",
            cluster_name="Text/OCR Content Retrieval Failures",
            core_problem="OCR text search failures",
            supporting_observation_ids=["R02"],
            count=1,
            what_users_remember="Text in image",
            what_is_missing="Metadata",
            typical_search_behavior="Keyword search",
            failure_point="OCR breakdown",
            workarounds="Manual browse",
            evidence_summary="Supported by 1 observation",
            open_questions_for_interviews=["Validation question"]
        ),
        ProblemCluster(
            cluster_id="CL-03",
            cluster_name="Result Relevance & Breadth Failures",
            core_problem="Relevance failures",
            supporting_observation_ids=["R05", "R07"],
            count=2,
            what_users_remember="Visual concept",
            what_is_missing="Exact tag",
            typical_search_behavior="Broad search",
            failure_point="Truncated results",
            workarounds="Give up",
            evidence_summary="Supported by 2 observations",
            open_questions_for_interviews=["Validation question"]
        ),
        ProblemCluster(
            cluster_id="CL-04",
            cluster_name="Navigation / Album Sync Delays",
            core_problem="Newly created album search indexing delay",
            supporting_observation_ids=["R06"],
            count=1,
            what_users_remember="Album title",
            what_is_missing="Sync status",
            typical_search_behavior="Search album name",
            failure_point="Indexing delay",
            workarounds="Wait and refresh",
            evidence_summary="Supported by 1 observation",
            open_questions_for_interviews=["Validation question"]
        ),
    ]

    opps = synthesize_opportunities(clusters)
    assert len(opps) == 4

    opp3 = next(o for o in opps if "R05" in o.supporting_evidence_ids or "R07" in o.supporting_evidence_ids)
    opp4 = next(o for o in opps if "R06" in o.supporting_evidence_ids)

    assert opp3.opportunity_id != opp4.opportunity_id
    assert opp3.opportunity_name.lower() != opp4.opportunity_name.lower()
    assert opp4.supporting_evidence_ids == ["R06"]
    assert any(term in opp4.opportunity_name.lower() or term in opp4.user_problem.lower() for term in ["album", "sync", "searchable", "created"])


def test_coverage_validation_and_repair_r03_r07():
    from backend.app.models.observation import StructuredObservation
    from backend.app.models.cluster import ProblemCluster
    from backend.app.services.clustering import validate_and_repair_cluster_coverage
    from backend.app.services.opportunities import synthesize_opportunities

    all_obs = [
        StructuredObservation(
            id="R01", source="Reddit", url="http://example.com/1",
            retrieval_scenario="Trying to retrieve older family photos using a remembered month/year.",
            user_statement="Date search fails.", problem_category="Metadata / date / location mismatch",
            evidence_strength="High", what_user_remembers="July 2016", what_user_forgot="Exact day",
            search_attempt="July 2016", search_behavior="Date query", retrieval_outcome="Zero results",
            failure_point="Date search zero results", workaround="Manual scroll", analyst_note="Grounded"
        ),
        StructuredObservation(
            id="R03", source="Reddit", url="http://example.com/3",
            retrieval_scenario="Trying to retrieve a specific photo/video using a remembered keyword or filename.",
            user_statement="Keyword searches no longer reliably find photos by name.", problem_category="Search understanding failure",
            evidence_strength="High", what_user_remembers="Filename", what_user_forgot="Metadata",
            search_attempt="keyword", search_behavior="Keyword search", retrieval_outcome="Missing item",
            failure_point="Filename search fails", workaround="Try random keywords", analyst_note="Grounded"
        ),
        StructuredObservation(
            id="R07", source="Reddit", url="http://example.com/7",
            retrieval_scenario="Trying to retrieve a group of photos using a remembered object or filename.",
            user_statement="Searches for common concepts return only a few photos.", problem_category="Search understanding failure",
            evidence_strength="High", what_user_remembers="Object concept", what_user_forgot="Date",
            search_attempt="dogs", search_behavior="Concept search", retrieval_outcome="Truncated results",
            failure_point="Truncated results", workaround="Give up", analyst_note="Grounded"
        )
    ]

    # Test 1: Cluster missing observations repair
    partial_clusters = [
        ProblemCluster(
            cluster_id="CL-01",
            cluster_name="Date-Based Retrieval & Indexing Failures",
            core_problem="Date index failures",
            supporting_observation_ids=["R01"],
            count=1,
            what_users_remember="Month/year", what_is_missing="Exact day",
            typical_search_behavior="Date query", failure_point="Zero results",
            workarounds="Manual scroll", evidence_summary="Supported by 1 obs",
            open_questions_for_interviews=["Question"]
        )
    ]

    repaired_clusters = validate_and_repair_cluster_coverage(all_obs, partial_clusters)
    covered_cluster_ids = {oid for c in repaired_clusters for oid in c.supporting_observation_ids}

    # Requirement 14a & 14c: All relevant observations covered, R03 and R07 not lost
    assert "R01" in covered_cluster_ids
    assert "R03" in covered_cluster_ids
    assert "R07" in covered_cluster_ids
    assert covered_cluster_ids == {"R01", "R03", "R07"}

    # Test 2: Opportunity synthesis evidence repair & coverage
    opps = synthesize_opportunities(repaired_clusters)
    covered_opp_ids = {eid for o in opps for eid in o.supporting_evidence_ids}

    # Requirement 14b: All relevant observations represented in opportunities
    assert "R01" in covered_opp_ids
    assert "R03" in covered_opp_ids
    assert "R07" in covered_opp_ids
    assert covered_opp_ids == {"R01", "R03", "R07"}

    # Requirement 14e: Evidence traceability check
    obs_map = {o.id: o.url for o in all_obs}
    for opp in opps:
        for eid in opp.supporting_evidence_ids:
            assert eid in obs_map
            assert obs_map[eid].startswith("http")


def test_pipeline_dataset_agnostic_sizes(monkeypatch):
    """
    Regression test meant to ensure the discovery pipeline handles datasets of arbitrary size:
    3, 12, 50, 1000, and 2000 observations dynamically without hard-coded assumptions or failures.
    """
    from backend.app.services.llm_client import llm_client
    monkeypatch.setattr(llm_client, "api_key", "")
    for size in [3, 12, 50, 1000, 2000]:
        raw_obs_list = []
        for i in range(1, size + 1):
            if i % 3 == 1:
                stmt = f"Date search for July {2010 + (i % 10)} fails to return my photos #{i}"
                scen = "Retrieving old vacation photos by date"
            elif i % 3 == 2:
                stmt = f"OCR text search for recipe text in photo fails to surface document #{i}"
                scen = "Retrieving document photo using remembered text"
            else:
                stmt = f"Search results for dog photo #{i} are incomplete"
                scen = "Retrieving visual concept"

            raw_obs_list.append(
                RawObservation(
                    id=f"OBS-{i:04d}",
                    source="Google Play",
                    url=f"https://play.google.com/store/apps/details?id=com.google.android.apps.photos&reviewId=OBS-{i:04d}",
                    user_statement=stmt,
                    retrieval_scenario=scen
                )
            )

        # 1. Stage 2 Relevance Filtering
        relevance_results = filter_relevance(raw_obs_list)
        assert len(relevance_results) == size, f"Expected {size} relevance results, got {len(relevance_results)}"
        relevance_map = {r.id: r for r in relevance_results}

        # 2. Stage 3 Extraction
        structured = extract_structured_observations(raw_obs_list, relevance_map=relevance_map)
        assert len(structured) == size, f"Expected {size} structured observations, got {len(structured)}"

        # 3. Stage 4 Clustering
        clusters = cluster_observations(structured)
        assert len(clusters) > 0, f"Expected at least 1 cluster for dataset size {size}"
        
        clustered_ids = {oid for c in clusters for oid in c.supporting_observation_ids}
        assert len(clustered_ids) == size, f"Expected all {size} observations to be covered in clusters"

        # 4. Stage 5 Opportunities
        opps = synthesize_opportunities(clusters)
        assert len(opps) > 0, f"Expected at least 1 opportunity area for dataset size {size}"

        opp_evidence_ids = {eid for o in opps for eid in o.supporting_evidence_ids}
        assert len(opp_evidence_ids) == size, f"Expected all {size} observations to be represented in opportunities"


def test_weak_and_ambiguous_observations_excluded_from_clusters_and_opportunities():
    """
    Regression test ensuring weak/ambiguous observations (e.g., problem_category == 'Other' or
    evidence_strength == 'Low') remain in the observation audit layer but are strictly excluded from
    clusters and opportunities.
    """
    from backend.app.models.observation import StructuredObservation
    from backend.app.services.clustering import cluster_observations
    from backend.app.services.opportunities import synthesize_opportunities

    valid_obs_1 = StructuredObservation(
        id="V01", source="Reddit", url="http://example.com/v1",
        retrieval_scenario="Date search gap",
        user_statement="Date search for July 2016 returns zero results.",
        problem_category="Metadata / date / location mismatch",
        evidence_strength="High",
        what_user_remembers="July 2016", what_user_forgot="Exact day",
        search_attempt="July 2016", search_behavior="Date query",
        retrieval_outcome="Zero results", failure_point="Date search zero results",
        workaround="Manual scroll", analyst_note="Grounded retrieval failure"
    )
    valid_obs_2 = StructuredObservation(
        id="V02", source="Reddit", url="http://example.com/v2",
        retrieval_scenario="Text OCR search gap",
        user_statement="Text search across images stopped finding documents with recognizable text.",
        problem_category="Search understanding failure",
        evidence_strength="High",
        what_user_remembers="In-image text", what_user_forgot="Metadata",
        search_attempt="Document text keyword", search_behavior="Keyword search",
        retrieval_outcome="Missing item", failure_point="OCR breakdown",
        workaround="Manual search", analyst_note="Grounded retrieval failure"
    )
    weak_obs_1 = StructuredObservation(
        id="W01", source="PlayStore", url="http://example.com/w1",
        retrieval_scenario="General search comment",
        user_statement="General feedback without explicit retrieval failure details.",
        problem_category="Other",
        evidence_strength="Low",
        what_user_remembers="General experience", what_user_forgot="N/A",
        search_attempt="General search", search_behavior="Broad query",
        retrieval_outcome="Unspecified", failure_point="General feedback without explicit retrieval failure details.",
        workaround="None", analyst_note="Weak/ambiguous observation"
    )
    weak_obs_2 = StructuredObservation(
        id="W02", source="PlayStore", url="http://example.com/w2",
        retrieval_scenario="Non-failure opinion",
        user_statement="Search should be better.",
        problem_category="Other",
        evidence_strength="Low",
        what_user_remembers="General idea", what_user_forgot="N/A",
        search_attempt="Search", search_behavior="Opinion",
        retrieval_outcome="Unspecified", failure_point="General non-failure feedback",
        workaround="None", analyst_note="Weak/ambiguous observation"
    )

    all_obs = [valid_obs_1, valid_obs_2, weak_obs_1, weak_obs_2]

    # Stage 4: Clustering
    clusters = cluster_observations(all_obs)
    
    # Assert clusters exist only for valid observations
    clustered_obs_ids = {oid for c in clusters for oid in c.supporting_observation_ids}
    assert "V01" in clustered_obs_ids
    assert "V02" in clustered_obs_ids
    assert "W01" not in clustered_obs_ids
    assert "W02" not in clustered_obs_ids

    # Stage 5: Opportunity synthesis
    opps = synthesize_opportunities(clusters)
    opp_evidence_ids = {eid for o in opps for eid in o.supporting_evidence_ids}
    assert "V01" in opp_evidence_ids
    assert "V02" in opp_evidence_ids
    assert "W01" not in opp_evidence_ids
    assert "W02" not in opp_evidence_ids

    # Test edge case: Dataset containing ONLY weak/ambiguous observations
    only_weak_clusters = cluster_observations([weak_obs_1, weak_obs_2])
    assert len(only_weak_clusters) == 0, "Weak observations alone must not generate any problem clusters"
    only_weak_opps = synthesize_opportunities(only_weak_clusters)
    assert len(only_weak_opps) == 0, "No opportunities must be synthesized when there are no valid clusters"


def test_scenario_inference_and_placeholder_cleaning():
    from backend.app.services.extraction import (
        is_placeholder_scenario,
        infer_scenario_from_evidence,
        extract_observation_fallback
    )

    # 1. Meaningful scenario -> preserved
    raw_meaningful = RawObservation(
        id="M01", source="Reddit", url="http://example.com/m1",
        user_statement="Searched by concept keyword but results were empty.",
        retrieval_scenario="Searching for beach vacation photos using keywords"
    )
    extracted_m = extract_observation_fallback(raw_meaningful)
    assert extracted_m.retrieval_scenario == "Searching for beach vacation photos using keywords"

    # 2. Blank / missing scenario -> inferred
    raw_blank = RawObservation(
        id="B01", source="Reddit", url="http://example.com/b1",
        user_statement="I tried searching for my old photos from July 2016 but nothing showed up.",
        retrieval_scenario="Not specified"
    )
    extracted_b = extract_observation_fallback(raw_blank)
    assert "Searching for photos using remembered date or timeframe" in extracted_b.retrieval_scenario

    # 3. Placeholder scenario ("Not specified — infer from user feedback") -> inferred
    raw_placeholder = RawObservation(
        id="P01", source="Reddit", url="http://example.com/p1",
        user_statement="Searching by concept keyword returns fewer results than expected.",
        retrieval_scenario="Not specified — infer from user feedback"
    )
    extracted_p = extract_observation_fallback(raw_placeholder)
    assert extracted_p.retrieval_scenario != "Not specified — infer from user feedback"
    assert "Not specified" not in extracted_p.retrieval_scenario
    assert "infer from user feedback" not in extracted_p.retrieval_scenario
    assert "concept" in extracted_p.retrieval_scenario.lower() or "photo" in extracted_p.retrieval_scenario.lower()

    # 4. Insufficient evidence / category 'Other' -> "Not mentioned" neutral fallback
    raw_insufficient = RawObservation(
        id="I01", source="PlayStore", url="http://example.com/i1",
        user_statement="This app is okay I guess.",
        retrieval_scenario="Not specified — infer from user feedback"
    )
    extracted_i = extract_observation_fallback(raw_insufficient)
    assert extracted_i.retrieval_scenario == "Not mentioned"


def test_traceability_inspector_uses_inferred_scenario():
    from backend.app.services.pipeline import RESULTS_CACHE, update_status, build_export_report
    from backend.app.models.observation import StructuredObservation
    from backend.app.models.cluster import ProblemCluster
    from backend.app.models.opportunity import OpportunityArea

    analysis_id = "test-analysis-traceability-001"
    update_status(analysis_id, "test-dataset", "Completed", 100, "completed", 1, 1, 1, 1)

    obs = StructuredObservation(
        id="T01", source="PlayStore", url="http://example.com/t01",
        retrieval_scenario="Searching for photos using remembered visual concept keywords",
        what_user_remembers="Visual concept", what_user_forgot="Exact date",
        search_attempt="Keyword search", search_behavior="Typing concept",
        retrieval_outcome="Incomplete subset", failure_point="Concept search retrieval gap.",
        workaround="Not mentioned", problem_category="Result relevance failure",
        evidence_strength="High", analyst_note="Grounded"
    )

    cluster = ProblemCluster(
        cluster_id="CL-01", cluster_name="Result Relevance & Breadth Failures",
        core_problem="Concept search gap", supporting_observation_ids=["T01"], count=1,
        what_users_remember="Visual concept", what_is_missing="Metadata",
        typical_search_behavior="Keyword search", failure_point="Incomplete results",
        workarounds="None", evidence_summary="Supported by 1 obs",
        open_questions_for_interviews=["How do you refine keyword searches?"]
    )

    opp = OpportunityArea(
        opportunity_id="OPP-01", opportunity_name="Opportunity to assist concept retrieval",
        user_problem="Concept search returns incomplete sets", supporting_evidence_ids=["T01"],
        retrieval_stage="Result Relevance", why_current_workaround_is_insufficient="Users give up",
        what_needs_to_be_validated=["Refinement behaviors"]
    )

    RESULTS_CACHE[analysis_id] = {
        "observations": [obs.model_dump()],
        "clusters": [cluster.model_dump()],
        "opportunities": [opp.model_dump()]
    }

    report = build_export_report(analysis_id)
    opp_trace = report.traceability_map["OPP-01"]
    supp_obs = opp_trace["supporting_observations"][0]

    assert supp_obs["id"] == "T01"
    assert supp_obs["retrieval_scenario"] == "Searching for photos using remembered visual concept keywords"
    assert "Not specified" not in supp_obs["retrieval_scenario"]
    assert "infer from user feedback" not in supp_obs["retrieval_scenario"]


def test_cluster_interview_questions_domain_alignment():
    from backend.app.models.observation import StructuredObservation
    from backend.app.services.clustering import cluster_observations

    concept_obs = StructuredObservation(
        id="C01", source="Reddit", url="http://example.com/c01",
        retrieval_scenario="Searching photos using visual concept",
        what_user_remembers="Visual concept terms", what_user_forgot="Metadata",
        search_attempt="Concept search", search_behavior="Submitting concept queries",
        retrieval_outcome="Fewer results returned", failure_point="Concept search retrieval gap.",
        workaround="Not mentioned", problem_category="Result relevance failure",
        evidence_strength="High", analyst_note="Grounded"
    )

    clusters = cluster_observations([concept_obs])
    assert len(clusters) == 1
    relevance_cluster = clusters[0]
    assert relevance_cluster.cluster_name == "Result Relevance & Breadth Failures"

    # Verify interview questions focus on visual concepts/keywords and do NOT ask about date retrieval
    questions_str = " ".join(relevance_cluster.open_questions_for_interviews).lower()
    assert "date's forgotten" not in questions_str
    assert "concept" in questions_str or "keyword" in questions_str or "visual" in questions_str


def test_pipeline_retains_all_input_records_in_audit_layer(monkeypatch):
    """
    Regression test verifying that 100% of input records (relevant OR irrelevant) remain
    in the structured observations audit layer, with no dropped IDs, while irrelevant reviews
    are excluded from clusters and opportunities.
    """
    from backend.app.services.llm_client import llm_client
    from backend.app.services.pipeline import RESULTS_CACHE, update_status, build_export_report
    monkeypatch.setattr(llm_client, "api_key", "")

    raw_obs_list = []
    # 10 valid retrieval failure records
    for i in range(1, 11):
        raw_obs_list.append(
            RawObservation(
                id=f"V-{i:02d}", source="Reddit", url=f"http://example.com/v{i}",
                user_statement=f"Date search for July {2010+i} fails to return photos #{i}",
                retrieval_scenario="Date search issue"
            )
        )
    # 2 irrelevant/noise records
    raw_obs_list.append(
        RawObservation(
            id="N-01", source="PlayStore", url="http://example.com/n1",
            user_statement="App update error 504 cannot download package",
            retrieval_scenario="App update issue"
        )
    )
    raw_obs_list.append(
        RawObservation(
            id="N-02", source="PlayStore", url="http://example.com/n2",
            user_statement="Buy Google One storage quota popups are annoying",
            retrieval_scenario="Storage quota complaint"
        )
    )

    assert len(raw_obs_list) == 12

    # Stage 2: Relevance
    relevance_results = filter_relevance(raw_obs_list)
    assert len(relevance_results) == 12
    relevance_map = {r.id: r for r in relevance_results}

    assert relevance_map["N-01"].relevant is False
    assert relevance_map["N-02"].relevant is False
    assert sum(1 for r in relevance_results if r.relevant) == 10

    # Stage 3: Extraction on ALL 12 records
    structured = extract_structured_observations(raw_obs_list, relevance_map=relevance_map)
    assert len(structured) == 12, "All 12 input records must be retained in structured observations"
    
    extracted_ids = {o.id for o in structured}
    input_ids = {o.id for o in raw_obs_list}
    assert extracted_ids == input_ids, "No input ID may be missing from the observation audit layer"

    # Verify irrelevant observations are marked appropriately
    n01_obs = next(o for o in structured if o.id == "N-01")
    assert n01_obs.problem_category == "Other"
    assert n01_obs.evidence_strength == "Low"

    # Stage 4: Clustering
    clusters = cluster_observations(structured)
    clustered_ids = {oid for c in clusters for oid in c.supporting_observation_ids}
    assert "N-01" not in clustered_ids, "Irrelevant observation N-01 must be excluded from clusters"
    assert "N-02" not in clustered_ids, "Irrelevant observation N-02 must be excluded from clusters"
    assert len(clustered_ids) == 10, "All 10 valid retrieval observations must enter clusters"

    # Stage 5: Opportunities
    opps = synthesize_opportunities(clusters)
    opp_evidence_ids = {eid for o in opps for eid in o.supporting_evidence_ids}
    assert "N-01" not in opp_evidence_ids, "Irrelevant observation N-01 must be excluded from opportunities"
    assert "N-02" not in opp_evidence_ids, "Irrelevant observation N-02 must be excluded from opportunities"
    assert len(opp_evidence_ids) == 10

    # Export report validation
    analysis_id = "test-export-audit-12"
    update_status(analysis_id, "test-ds", "Completed", 100, "completed", 12, 10, len(clusters), len(opps))
    RESULTS_CACHE[analysis_id] = {
        "observations": [o.model_dump() for o in structured],
        "clusters": [c.model_dump() for c in clusters],
        "opportunities": [o.model_dump() for o in opps]
    }
    report = build_export_report(analysis_id)
    assert report.total_observations == 12
    assert report.relevant_count == 10
    assert len(report.observations) == 12


def test_specific_date_searches_after_update_relevance_classification():
    """
    Verifies that user statements describing search failures after updates
    (e.g., 'specific-date searches stopped working after a recent update')
    are correctly classified as relevant search failure evidence rather than trapped as noise.
    """
    obs = RawObservation(
        id="GS04_TEST",
        source="GoogleSupport",
        url="https://support.google.com/photos/thread/348117640",
        user_statement="The user says specific-date searches stopped working after a recent update and that changing date formats did not restore the expected results.",
        retrieval_scenario="Trying to retrieve photos by a remembered day/month after a search experience change."
    )

    results = filter_relevance([obs])
    assert len(results) == 1
    assert results[0].relevant is True, "Date search failure mentioning update must be classified as relevant"


def test_semantic_consistency_across_all_retrieval_domains():
    """
    Regression test ensuring 100% semantic consistency between Retrieval Scenario
    and the remaining 14 extracted fields across all 6 retrieval domains.
    """
    from backend.app.services.extraction import extract_observation_fallback, detect_observation_domain

    test_fixtures = [
        # (id, statement, scenario, expected_domain, expected_category)
        ("D01", "I tried searching for my 2019 trip photos by date but got zero results.", "Trying to retrieve photos by date.", "date", "Metadata / date / location mismatch"),
        ("T01", "Text search inside image failed to find my recipe document.", "Trying to retrieve document by in-image text.", "ocr", "Search understanding failure"),
        ("K01", "Searching for photo by filename vacation.jpg returned no results.", "Trying to find photo by exact filename.", "filename", "Retrieval / indexing failure"),
        ("A01", "My newly created album does not appear in album search.", "Accessing newly created album.", "album", "Navigation / browsing failure"),
        ("V01", "Searching for dogs returns an incomplete unrefined subset of photos.", "Visual concept search for objects.", "relevance", "Result relevance failure"),
        ("I01", "This app is great, love using it.", "Generic positive review.", "other", "Other"),
    ]

    for id_, stmt, scen, exp_domain, exp_cat in test_fixtures:
        raw = RawObservation(id=id_, source="Test", url="http://example.com", user_statement=stmt, retrieval_scenario=scen)
        det_domain = detect_observation_domain(stmt, scen)
        assert det_domain == exp_domain, f"Failed domain detection for {id_}: expected {exp_domain}, got {det_domain}"

        extracted = extract_observation_fallback(raw)
        assert extracted.problem_category == exp_cat, f"Failed category for {id_}: expected {exp_cat}, got {extracted.problem_category}"

        # Cross-field domain consistency assertions
        if exp_domain == "date":
            assert "concept" not in extracted.failure_point.lower()
            assert "concept" not in extracted.what_user_remembers.lower()
            assert "date" in extracted.failure_point.lower() or "filtering" in extracted.failure_point.lower()
        elif exp_domain == "ocr":
            assert "ocr" in extracted.failure_point.lower() or "text" in extracted.failure_point.lower()
        elif exp_domain == "filename":
            assert "filename" in extracted.failure_point.lower() or "keyword" in extracted.failure_point.lower()
        elif exp_domain == "album":
            assert "album" in extracted.failure_point.lower() or "sync" in extracted.failure_point.lower()


def test_catch_date_scenario_with_concept_category_mismatch_bug():
    """
    Catches the exact class of bug where scenario describes date retrieval,
    but category/failure point is incorrectly set to visual concept search.
    """
    from backend.app.models.observation import StructuredObservation
    from backend.app.services.extraction import validate_and_enforce_semantic_consistency

    raw_obs = RawObservation(
        id="GS04_BUG_CHECK",
        source="GoogleSupport",
        url="http://example.com/gs04",
        user_statement="The user says specific-date searches stopped working after a recent update and that changing date formats did not restore expected results.",
        retrieval_scenario="Trying to retrieve photos by a remembered day/month after a search experience change."
    )

    # Simulate an inconsistent extracted observation (date scenario, concept search fields)
    inconsistent_obs = StructuredObservation(
        id="GS04_BUG_CHECK",
        source="GoogleSupport",
        url="http://example.com/gs04",
        retrieval_scenario="Trying to retrieve photos by a remembered day/month after a search experience change.",
        what_user_remembers="Remembers general visual concepts or objects.",
        what_user_forgot="Not mentioned",
        search_attempt="Searching by concept keyword.",
        search_behavior="Submitting concept search queries.",
        retrieval_outcome="Fewer results returned than expected.",
        failure_point="Concept search retrieval gap.",
        workaround="Not mentioned",
        problem_category="Search understanding failure",
        evidence_strength="High",
        analyst_note="Raw extraction"
    )

    realigned_obs = validate_and_enforce_semantic_consistency(raw_obs, inconsistent_obs)

    # Verify that inconsistency was caught and corrected
    assert realigned_obs.problem_category == "Metadata / date / location mismatch"
    assert "concept" not in realigned_obs.failure_point.lower()
    assert "concept" not in realigned_obs.what_user_remembers.lower()
    assert "date" in realigned_obs.failure_point.lower()
    assert realigned_obs.retrieval_scenario == "Trying to retrieve photos by a remembered day/month after a search experience change."


def test_no_stale_evidence_ids_between_analyses():
    """
    Test A: Run pilot dataset, then run a separate custom dataset with completely different IDs.
    Verify second analysis contains ZERO IDs from first analysis.
    """
    from backend.app.services.clustering import cluster_observations
    from backend.app.services.opportunities import synthesize_opportunities
    from backend.app.services.pipeline import validate_current_analysis_evidence
    from backend.app.models.observation import StructuredObservation

    pilot_obs = [
        StructuredObservation(
            id="R01", source="Reddit", url="http://example.com/r01",
            retrieval_scenario="Date search issue", user_statement="July 2016 search failed.",
            problem_category="Metadata / date / location mismatch", evidence_strength="High",
            what_user_remembers="July 2016", what_user_forgot="Day", search_attempt="July 2016",
            search_behavior="Date query", retrieval_outcome="Zero results",
            failure_point="Date search zero results", workaround="Scroll", analyst_note="Grounded"
        )
    ]
    clusters_1 = cluster_observations(pilot_obs)
    opps_1 = synthesize_opportunities(clusters_1)
    metrics_1 = validate_current_analysis_evidence(clusters_1, opps_1, pilot_obs)
    assert metrics_1["invalid_stale_evidence_ids"] == 0

    custom_obs = [
        StructuredObservation(
            id="UUID-1001-NEW", source="GooglePlay", url="http://example.com/custom1",
            retrieval_scenario="Text OCR issue", user_statement="Text in recipe photo search failed.",
            problem_category="Search understanding failure", evidence_strength="High",
            what_user_remembers="Recipe text", what_user_forgot="Date", search_attempt="Recipe text",
            search_behavior="Keyword search", retrieval_outcome="Missing item",
            failure_point="OCR breakdown", workaround="Manual browse", analyst_note="Grounded"
        ),
        StructuredObservation(
            id="UUID-1002-NEW", source="GooglePlay", url="http://example.com/custom2",
            retrieval_scenario="Date search issue", user_statement="Searching 2020 photos returns nothing.",
            problem_category="Metadata / date / location mismatch", evidence_strength="High",
            what_user_remembers="2020", what_user_forgot="Day", search_attempt="2020",
            search_behavior="Date query", retrieval_outcome="Zero results",
            failure_point="Date search failure", workaround="Scroll", analyst_note="Grounded"
        )
    ]
    clusters_2 = cluster_observations(custom_obs)
    opps_2 = synthesize_opportunities(clusters_2)
    metrics_2 = validate_current_analysis_evidence(clusters_2, opps_2, custom_obs)
    assert metrics_2["invalid_stale_evidence_ids"] == 0

    pilot_ids = {"R01", "GS01", "GS02", "GS03", "GS04", "GS05"}
    custom_cluster_ids = {eid for c in clusters_2 for eid in c.supporting_observation_ids}
    custom_opp_ids = {eid for o in opps_2 for eid in o.supporting_evidence_ids}

    assert len(custom_cluster_ids.intersection(pilot_ids)) == 0
    assert len(custom_opp_ids.intersection(pilot_ids)) == 0


def test_cluster_evidence_belongs_to_current_dataset():
    """
    Test B: Generate clusters and assert every evidence ID is in current dataset.
    """
    from backend.app.services.clustering import cluster_observations
    from backend.app.models.observation import StructuredObservation

    custom_obs = [
        StructuredObservation(
            id="CUST-01", source="GooglePlay", url="http://example.com/c1",
            retrieval_scenario="Searching by visual concept", user_statement="Searching dog photos fails.",
            problem_category="Search understanding failure", evidence_strength="High",
            what_user_remembers="Dog", what_user_forgot="Date", search_attempt="dogs",
            search_behavior="Keyword query", retrieval_outcome="Incomplete subset",
            failure_point="Concept search failure", workaround="Give up", analyst_note="Grounded"
        )
    ]
    clusters = cluster_observations(custom_obs)
    current_dataset_ids = {o.id for o in custom_obs}

    for c in clusters:
        for eid in c.supporting_observation_ids:
            assert eid in current_dataset_ids


def test_opportunity_evidence_belongs_to_current_clusters():
    """
    Test C: Assert every opportunity evidence ID exists in its parent cluster.
    """
    from backend.app.services.clustering import cluster_observations
    from backend.app.services.opportunities import synthesize_opportunities
    from backend.app.models.observation import StructuredObservation

    custom_obs = [
        StructuredObservation(
            id="CUST-02", source="GooglePlay", url="http://example.com/c2",
            retrieval_scenario="Album search sync delay", user_statement="Created album not in search.",
            problem_category="Navigation / browsing failure", evidence_strength="High",
            what_user_remembers="Album title", what_user_forgot="Sync status", search_attempt="Album title",
            search_behavior="Search album name", retrieval_outcome="Not found",
            failure_point="Album sync delay", workaround="Refresh", analyst_note="Grounded"
        )
    ]
    clusters = cluster_observations(custom_obs)
    opps = synthesize_opportunities(clusters)

    cluster_obs_ids = {eid for c in clusters for eid in c.supporting_observation_ids}

    for opp in opps:
        for eid in opp.supporting_evidence_ids:
            assert eid in cluster_obs_ids


def test_other_observations_never_enter_clusters():
    """
    Test D: Use generic/non-retrieval reviews and verify they remain Other/Low and are excluded.
    """
    from backend.app.services.clustering import cluster_observations
    from backend.app.services.opportunities import synthesize_opportunities
    from backend.app.models.observation import StructuredObservation

    other_obs = [
        StructuredObservation(
            id="OTHER-01", source="PlayStore", url="http://example.com/o1",
            retrieval_scenario="App crash complaint", user_statement="App keeps crashing on startup.",
            problem_category="Other", evidence_strength="Low",
            what_user_remembers="N/A", what_user_forgot="N/A", search_attempt="N/A",
            search_behavior="N/A", retrieval_outcome="Crash", failure_point="App crash",
            workaround="Reinstall", analyst_note="Non-retrieval complaint"
        ),
        StructuredObservation(
            id="OTHER-02", source="PlayStore", url="http://example.com/o2",
            retrieval_scenario="Storage quota complaint", user_statement="Storage popup annoying.",
            problem_category="Other", evidence_strength="Low",
            what_user_remembers="N/A", what_user_forgot="N/A", search_attempt="N/A",
            search_behavior="N/A", retrieval_outcome="Popup", failure_point="Quota popup",
            workaround="Ignore", analyst_note="Non-retrieval complaint"
        )
    ]

    clusters = cluster_observations(other_obs)
    assert len(clusters) == 0, "No clusters should be generated for Other/Low evidence observations"

    opps = synthesize_opportunities(clusters)
    assert len(opps) == 0, "No opportunities should be generated when there are no clusters"


def test_custom_dataset_does_not_use_preset_fallback():
    """
    Test E: Upload custom dataset and verify no preset/pilot observation ID appears anywhere in results.
    """
    from backend.app.models.dataset import RawObservation
    from backend.app.services.relevance import filter_relevance
    from backend.app.services.extraction import extract_structured_observations
    from backend.app.services.clustering import cluster_observations
    from backend.app.services.opportunities import synthesize_opportunities

    custom_raw = [
        RawObservation(
            id="CUSTOM-999", source="GooglePlay", url="http://example.com/c999",
            user_statement="I tried searching for my recipe document text but search returned zero photos.",
            retrieval_scenario="Searching for document by in-image text"
        )
    ]

    relevance_results = filter_relevance(custom_raw)
    rel_map = {r.id: r for r in relevance_results}
    structured = extract_structured_observations(custom_raw, relevance_map=rel_map)
    clusters = cluster_observations(structured)
    opps = synthesize_opportunities(clusters)

    pilot_ids = {"R01", "R02", "R03", "R04", "R05", "R06", "R07", "GS01", "GS02", "GS03", "GS04", "GS05"}

    all_res_ids = {o.id for o in structured}
    all_res_ids.update({eid for c in clusters for eid in c.supporting_observation_ids})
    all_res_ids.update({eid for o in opps for eid in o.supporting_evidence_ids})

    assert len(all_res_ids.intersection(pilot_ids)) == 0


def test_analysis_state_isolation():
    """
    Test F: Run two analyses sequentially and verify result objects, IDs, and evidence mappings
    are completely isolated.
    """
    from backend.app.services.pipeline import update_status, RESULTS_CACHE, build_export_report
    from backend.app.models.observation import StructuredObservation
    from backend.app.models.cluster import ProblemCluster
    from backend.app.models.opportunity import OpportunityArea

    analysis_id_1 = "analysis-iso-001"
    analysis_id_2 = "analysis-iso-002"

    obs_1 = [
        StructuredObservation(
            id="SET1-01", source="Source1", url="http://example.com/1",
            retrieval_scenario="Scenario 1", user_statement="Statement 1",
            problem_category="Search understanding failure", evidence_strength="High",
            what_user_remembers="R1", what_user_forgot="F1", search_attempt="S1",
            search_behavior="B1", retrieval_outcome="O1", failure_point="FP1",
            workaround="W1", analyst_note="N1"
        )
    ]
    cl_1 = [
        ProblemCluster(
            cluster_id="CL-01", cluster_name="Cluster 1", core_problem="P1",
            supporting_observation_ids=["SET1-01"], count=1, what_users_remember="R1",
            what_is_missing="F1", typical_search_behavior="B1", failure_point="FP1",
            workarounds="W1", evidence_summary="Supported by 1 obs", open_questions_for_interviews=[]
        )
    ]
    opp_1 = [
        OpportunityArea(
            opportunity_id="OPP-01", opportunity_name="Opp 1", user_problem="UP1",
            supporting_evidence_ids=["SET1-01"], retrieval_stage="Stage 1",
            why_current_workaround_is_insufficient="W1", what_needs_to_be_validated=[]
        )
    ]

    update_status(analysis_id_1, "ds-1", "Completed", 100, "completed", 1, 1, 1, 1)
    RESULTS_CACHE[analysis_id_1] = {
        "observations": [o.model_dump() for o in obs_1],
        "clusters": [c.model_dump() for c in cl_1],
        "opportunities": [o.model_dump() for o in opp_1]
    }

    obs_2 = [
        StructuredObservation(
            id="SET2-01", source="Source2", url="http://example.com/2",
            retrieval_scenario="Scenario 2", user_statement="Statement 2",
            problem_category="Metadata / date / location mismatch", evidence_strength="High",
            what_user_remembers="R2", what_user_forgot="F2", search_attempt="S2",
            search_behavior="B2", retrieval_outcome="O2", failure_point="FP2",
            workaround="W2", analyst_note="N2"
        )
    ]
    cl_2 = [
        ProblemCluster(
            cluster_id="CL-01", cluster_name="Cluster 2", core_problem="P2",
            supporting_observation_ids=["SET2-01"], count=1, what_users_remember="R2",
            what_is_missing="F2", typical_search_behavior="B2", failure_point="FP2",
            workarounds="W2", evidence_summary="Supported by 1 obs", open_questions_for_interviews=[]
        )
    ]
    opp_2 = [
        OpportunityArea(
            opportunity_id="OPP-01", opportunity_name="Opp 2", user_problem="UP2",
            supporting_evidence_ids=["SET2-01"], retrieval_stage="Stage 2",
            why_current_workaround_is_insufficient="W2", what_needs_to_be_validated=[]
        )
    ]

    update_status(analysis_id_2, "ds-2", "Completed", 100, "completed", 1, 1, 1, 1)
    RESULTS_CACHE[analysis_id_2] = {
        "observations": [o.model_dump() for o in obs_2],
        "clusters": [c.model_dump() for c in cl_2],
        "opportunities": [o.model_dump() for o in opp_2]
    }

    report_1 = build_export_report(analysis_id_1)
    report_2 = build_export_report(analysis_id_2)

    obs_1_id = report_1.observations[0].id if hasattr(report_1.observations[0], "id") else report_1.observations[0]["id"]
    obs_2_id = report_2.observations[0].id if hasattr(report_2.observations[0], "id") else report_2.observations[0]["id"]
    assert obs_1_id == "SET1-01"
    assert obs_2_id == "SET2-01"
    report_1_ids = [getattr(o, "id", o.get("id") if isinstance(o, dict) else "") for o in report_1.observations]
    report_2_ids = [getattr(o, "id", o.get("id") if isinstance(o, dict) else "") for o in report_2.observations]
    assert "SET2-01" not in report_1_ids
    assert "SET1-01" not in report_2_ids




