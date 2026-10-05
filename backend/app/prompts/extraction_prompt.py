def get_extraction_prompt(id_: str, source: str, url: str, statement: str, scenario: str) -> str:
    return f"""SYSTEM: You are an expert qualitative research analyst. Convert the verbatim user statement into 14 structured research fields.

STRICT GROUNDING & EXTRACTION RULES:
1. Extract ONLY facts explicitly stated or directly described in the user statement.
2. If a field (e.g. what_user_remembers, what_user_forgot, search_attempt, search_behavior, or workaround) is NOT explicitly mentioned or clearly implied in the statement, output EXACTLY "Not mentioned". Do NOT invent or assume details.
3. NEVER output generic or repetitive template strings such as:
   - "Searching for photos using remembered visual concepts or object keywords"
   - "Inability to refine broad search results or concept retrieval gap."
   - "Remembers visual concept, person name, or object."
   - "Broad concept or person search."
   - "Submitting concept search queries."
   - "Search returns incomplete or unrefined results."
   Every field MUST be grounded specifically in the exact user statement.
4. RETRIEVAL SCENARIO RULE:
   - Ground the retrieval scenario strictly in the actual statement.
   - If input scenario is explicit, preserve it. Otherwise, generate a concise 1-sentence scenario describing the user's specific retrieval goal from their statement (e.g. "Searching for repair photos using text/subject terms").
5. FAILURE POINT RULE:
   - failure_point MUST describe the specific failure reported in the user statement (e.g. "Text search for 'Car Engine' returned only 15 out of 100s of photos", "Face detection reset and failed to identify familiar faces").
6. Assign problem_category to EXACTLY ONE of the following 9 taxonomy categories based strictly on evidence:
   - "Memory expression failure"
   - "Search understanding failure"
   - "Retrieval / indexing failure"
   - "Result relevance failure"
   - "Result evaluation failure"
   - "Search refinement failure"
   - "Navigation / browsing failure"
   - "Metadata / date / location mismatch"
   - "Other"

INPUT OBSERVATION:
ID: {id_}
Source: {source}
URL: {url}
Statement: "{statement}"
Input Scenario: "{scenario}"

OUTPUT FORMAT (JSON ONLY):
{{
  "id": "{id_}",
  "source": "{source}",
  "url": "{url}",
  "retrieval_scenario": "Concise 1-sentence retrieval goal grounded in statement",
  "what_user_remembers": "Explicit memory clues stated by user, or 'Not mentioned'",
  "what_user_forgot": "Explicitly stated forgotten context, or 'Not mentioned'",
  "search_attempt": "Explicit search query or action taken, or 'Not mentioned'",
  "search_behavior": "Explicitly observed search behavior, or 'Not mentioned'",
  "retrieval_outcome": "Actual retrieval outcome reported in statement",
  "failure_point": "Specific failure point described in user statement",
  "workaround": "User workaround explicitly stated, or 'Not mentioned'",
  "problem_category": "One of the 9 taxonomy categories listed above",
  "evidence_strength": "High|Medium|Low",
  "analyst_note": "Objective extraction note grounded strictly in quote"
}}
"""
