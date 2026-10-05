def get_clustering_prompt(observations_json: str) -> str:
    return f"""SYSTEM: You are a Principal Product Manager on Google Photos analyzing qualitative user evidence.
TASK: Group the provided structured observations into distinct recurring problem clusters based on shared retrieval failure modes, memory gaps, and search behaviors.

CRITICAL RULES:
1. EVERY input observation ID MUST be included in at least one cluster's supporting_observation_ids array. DO NOT leave out or silently drop ANY input observation ID. You MUST ONLY use observation IDs present in the input JSON below.
2. Group observations into distinct problem categories based on failure modes:
   - Date / Temporal Retrieval & Indexing Failures (e.g. date search failures, month/year range issues)
   - Text / OCR Content Retrieval Failures (e.g. searching text inside images/documents/slides)
   - Result Relevance & Breadth Failures (e.g. keyword searches failing, filename searches failing, unrefined/truncated subsets, missing results for common concept terms)
   - Navigation / Album Sync Delays (e.g. newly created album search indexing delays)
3. Do NOT merge Navigation / Album Sync into general search relevance. Keep Navigation / Album Sync Delays as a distinct cluster.
4. Do NOT invent supporting evidence or observation IDs not present in the input. NEVER use observation IDs from any other dataset or previous prompt.
5. If an observation fits multiple problem areas, it may be assigned to multiple clusters if relevant, but EVERY observation must appear in AT LEAST ONE cluster.
6. Include 3-4 open questions per cluster to validate in 5-6 user interviews.
   IMPORTANT: Each interview question MUST be derived directly from the specific problem area and evidence of THAT cluster. For example, for "Result Relevance & Breadth Failures", focus on visual concepts, keyword refinement, and incomplete result sets—do NOT ask about date filtering or timestamps unless dates are explicitly part of that cluster's core evidence.

INPUT STRUCTURED OBSERVATIONS:
{observations_json}

OUTPUT FORMAT (JSON ONLY):
[
  {{
    "cluster_id": "CL-01",
    "cluster_name": "Short descriptive title (e.g., Date-Based Retrieval & Indexing Failures, Navigation / Album Sync Delays)",
    "core_problem": "Detailed description of the core retrieval problem",
    "supporting_observation_ids": ["ID-001", "ID-002"],
    "count": 2,
    "what_users_remember": "Common remembered clues across cluster",
    "what_is_missing": "Common missing metadata or context across cluster",
    "typical_search_behavior": "Dominant search attempt pattern",
    "failure_point": "Primary point of failure",
    "workarounds": "Summary of workarounds mentioned",
    "evidence_summary": "Summary grounded strictly in supporting evidence",
    "open_questions_for_interviews": [
      "Targeted interview validation question 1",
      "Targeted interview validation question 2"
    ]
  }}
]
"""




