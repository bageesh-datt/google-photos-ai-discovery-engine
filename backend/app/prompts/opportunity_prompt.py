def get_opportunity_prompt(clusters_json: str) -> str:
    return f"""SYSTEM: Synthesize recurring problem clusters into broad research opportunity areas for qualitative user interview validation.

STRICT BOUNDARY AND SYNTHESIS RULES:
1. Synthesize exactly ONE distinct research opportunity per input cluster in matching order.
2. Cluster boundaries are authoritative inputs. The supporting_evidence_ids for an opportunity MUST contain ALL supporting_observation_ids from the specific input cluster being synthesized. Do NOT leave out any observation IDs from the cluster evidence.
3. Every opportunity MUST be derived directly from its parent cluster. The opportunity title, user problem space, workaround failure, and validation hypotheses MUST remain strictly aligned with the core problem of the parent cluster (e.g. Date/Temporal indexing, OCR/Text search, Result Relevance/Breadth, and Navigation/Album Sync indexing delays). Do NOT introduce unrelated topics (e.g. do not introduce date filtering into a visual concept relevance cluster).
4. Do NOT propose specific product features or UI solutions (e.g. do NOT say "Build an AI search button").
5. Do NOT rank or score opportunities by priority.
6. Frame purely as problem/research discovery spaces (e.g. "Opportunity to improve retrieval when...").
7. Every supporting_evidence_id in supporting_evidence_ids MUST exist in the supporting_observation_ids of the parent cluster. Never include IDs from outside the parent cluster or previous pilot/test datasets.

INPUT CLUSTERS:
{clusters_json}

OUTPUT FORMAT (JSON ONLY):
[
  {{
    "opportunity_id": "OPP-01",
    "opportunity_name": "Broad research opportunity title reflecting cluster problem",
    "user_problem": "Detailed problem space statement describing user friction",
    "supporting_evidence_ids": ["ID-001", "ID-002"],
    "retrieval_stage": "Affected retrieval stage (e.g. Memory Expression, Indexing, Navigation & Sync)",
    "why_current_workaround_is_insufficient": "Analysis of why current workarounds create user friction",
    "what_needs_to_be_validated": [
      "Hypothesis/question 1 for user interviews",
      "Hypothesis/question 2 for user interviews"
    ]
  }}
]
"""
