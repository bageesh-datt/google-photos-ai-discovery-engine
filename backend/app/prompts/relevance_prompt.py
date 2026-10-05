def get_relevance_prompt(id_: str, statement: str, scenario: str) -> str:
    return f"""SYSTEM: You are a senior product research analyst on the Core Experience team at Google Photos.
TASK: Determine if the following user observation contains EXPLICIT EVIDENCE that the user experienced a problem, friction, or failure when attempting to FIND, SEARCH, DISCOVER, or RETRIEVE a photo, video, document, or album.

STRICT RELEVANCE CRITERIA:

Mark "relevant": true ONLY IF ALL of the following are met:
1. The user is actively attempting to find, retrieve, or search photos/videos (or documents/albums) they believe exist, OR searching using a remembered clue (date, person, face, location, OCR text inside image, filename, visual object).
2. AND there is explicit evidence of difficulty, failure, mismatch, missing result, zero result, wrong result, incomplete result, or retrieval friction.

Mark "relevant": false IF the observation is ANY of the following:
1. Positive praise or rating (e.g. "good app", "very nice", "love this app", "useful", "great backup", "search is good") without reporting a retrieval failure.
2. Generic words like "photos", "search", "find", "backup", "album" used in positive praise or general feedback without a retrieval failure.
3. Reviews about sharing or partner sharing (e.g. "can't share photo link", "partner sharing").
4. Storage pricing, Google One subscriptions, or storage quota complaints (e.g. "15GB full", "intimidated to buy storage").
5. Backup and sync complaints without explicit photo search/retrieval failure context (e.g. "nagging to backup", "backup paused").
6. Photo editing, filters, unblur, Magic Eraser, or background music issues (e.g. "unblur has lines", "change memory music").
7. Downloading or exporting photos to PC or external storage.
8. Account login, permissions, password, or privacy settings.
9. Generic UI/UX, widgets, app update notifications, crashes, battery drain, or camera hardware issues.
10. General album organization or folder complaints without an explicit photo search/retrieval problem.

INPUT:
Observation ID: {id_}
User Statement: "{statement}"
Retrieval Scenario: "{scenario}"

OUTPUT FORMAT (JSON ONLY):
{{
  "relevant": true|false,
  "reason": "Short 1-sentence evidence-based explanation"
}}
"""
