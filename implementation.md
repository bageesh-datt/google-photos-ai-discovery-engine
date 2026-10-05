# Google Photos AI-Powered Discovery Engine — Implementation Specification

## 1. Implementation Objective

The objective of this implementation plan is to define the exact, step-by-step engineering execution strategy for building **Part 1 — AI-Powered Discovery Engine**. 

The engine is an internal research and problem-discovery system designed to systematically transform unstructured public user conversations (from Reddit, App Stores, Support Forums, etc.) about vague photo retrieval into structured, evidence-backed research insights:

$$\text{Raw User Evidence} \longrightarrow \text{Structured Retrieval Observations} \longrightarrow \text{Recurring Problem Patterns} \longrightarrow \text{Potential Opportunity Areas}$$

### Scope Boundaries:
- **In Scope (Part 1)**: Data ingestion, AI relevance filtering, structured LLM extraction, problem taxonomy categorization, evidence-backed clustering, opportunity synthesis, evidence traceability, and an internal research web dashboard.
- **Out of Scope**: Final consumer-facing Google Photos feature designs, product solutions, investment/product recommendations, solution ranking, or direct integration with Google Photos user media.

---

## 2. Tech Stack

To keep the system modular, maintainable, and aligned strictly with `architecture.md` without introducing unnecessary complexity, the following stack will be used:

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | React + Vite + Vanilla CSS | Modern, lightweight, fast UI development for an internal research dashboard. |
| **Backend API** | Python 3.11+ FastAPI + Uvicorn | Asynchronous processing, native Pydantic schema validation, rapid API endpoint creation. |
| **Data & Schema Validation** | Pydantic v2 | Strict JSON schema parsing and normalization of LLM outputs and API payloads. |
| **LLM Integration** | Configurable LLM Provider (e.g. Gemini API or OpenAI API) | Configurable via environment variables (`LLM_API_KEY`, `LLM_MODEL`). Implementation selects ONE active provider based on environment configuration to avoid unnecessary complexity. |
| **Storage Layer** | Local Filesystem (`CSV` for raw datasets; `JSON` for processing state, observations, clusters, opportunities) | Zero-database overhead for initial MVP and pilot scaling up to 100+ records. |
| **Cloud Deployment** | Render / Railway / Vercel | Public web deployment enabling 1-click reviewer testing via live URL. |
| **Testing** | `pytest`, `httpx` (FastAPI `TestClient`) | Unit testing and endpoint integration testing with LLM mocking. |

---

## 3. Project Folder Structure

```text
google-photos-discovery-engine/
├── problemStatement.md
├── architecture.md
├── implementation.md
├── README.md
├── .env.example
├── requirements.txt
│
├── data/
│   ├── raw/                      # Saved uploaded raw CSV datasets
│   ├── processed/                # Normalized raw dataset records
│   └── sample_observations.csv   # Pilot dataset (10–15 sample records)
│
├── backend/
│   └── app/
│       ├── main.py               # FastAPI app initialization, CORS, middleware
│       ├── config.py             # Environment variables (LLM settings, storage paths)
│       ├── models/               # Domain & Pydantic data models
│       │   ├── dataset.py        # Dataset & raw observation models
│       │   ├── observation.py    # Structured analysis schema
│       │   ├── cluster.py        # Cluster models
│       │   └── opportunity.py    # Opportunity area models
│       ├── schemas/              # API Request/Response JSON schemas
│       │   ├── dataset_schema.py
│       │   └── analysis_schema.py
│       ├── routes/               # FastAPI route handlers
│       │   ├── dataset_routes.py
│       │   └── analysis_routes.py
│       ├── services/             # Core business logic modules
│       │   ├── ingestion.py      # CSV validation & parsing
│       │   ├── relevance.py      # Stage 1: Relevance filtering service
│       │   ├── extraction.py     # Stage 2: LLM observation extraction service
│       │   ├── clustering.py     # Stage 3: Semantic clustering service
│       │   ├── opportunities.py  # Stage 4: Opportunity area synthesis service
│       │   └── llm_client.py     # Unified LLM provider client wrapper
│       └── prompts/              # Centralized prompt templates
│           ├── relevance_prompt.py
│           ├── extraction_prompt.py
│           ├── clustering_prompt.py
│           └── opportunity_prompt.py
│
├── frontend/                     # Internal Research Dashboard (React + Vite)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── FileUpload.jsx
│       │   ├── ProgressStepper.jsx
│       │   ├── ObservationTable.jsx
│       │   ├── ClusterCard.jsx
│       │   └── OpportunityCard.jsx
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── AnalysisView.jsx
│       │   └── ResultsView.jsx
│       └── services/
│           └── api.js            # Axios/Fetch backend API client
│
└── output/                       # Structured JSON analysis outputs
    ├── observations/             # Stored extraction JSONs by analysis_id
    ├── clusters/                 # Stored cluster JSONs by analysis_id
    └── opportunities/            # Stored opportunity JSONs by analysis_id
```

---

## 4. Data Input Format and Schema

The input data will be provided via CSV files containing raw user conversations collected from public sources (Reddit, Google Play Store, App Store, Support Forums, Social Media).

### CSV Column Definitions

| Column Name | Data Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `id` | String | Yes | Unique observation code | `R01` |
| `source` | String | Yes | Source platform | `Reddit` |
| `url` | String | Yes | Verifiable public URL | `https://reddit.com/r/googlephotos/...` |
| `user_statement` | String | Yes | Exact user quote or verbatim text | `"I remember a photo from my Goa trip in 2021..."` |
| `retrieval_scenario` | String | Yes | Contextual task description | `"Find old Goa trip photo without exact date"` |

### Validation Rules
1. Non-empty check on `id`, `user_statement`, and `source`.
2. URL format validation (must start with `http://` or `https://`).
3. Unique ID constraint across rows within a single upload.

---

## 5. Data Ingestion Workflow

- **What needs to be built**: CSV dataset parser, schema validator, and deduplication pipeline.
- **Module File**: `backend/app/services/ingestion.py`
- **Input**: Uploaded file stream (`.csv`).
- **Output**: JSON payload with `dataset_id`, validated row count, array of `RawObservation` objects, and validation errors (if any).
- **Connection to Next Component**: Validated raw observations are saved to `data/raw/{dataset_id}.json` and passed directly to the Relevance Filtering service.

### Execution Steps:
1. `POST /api/datasets/upload` receives file via FastAPI `UploadFile`.
2. `ingestion.py` reads CSV stream using Python's native `csv.DictReader`.
3. Each record is validated against `RawObservation` Pydantic model.
4. Duplicates are removed based on identical `id` or normalized `user_statement` text.
5. Invalid rows are logged in an `errors` list returned in the upload summary response.
6. Clean dataset is assigned a UUID `dataset_id` and saved to `data/raw/{dataset_id}.json`.

---

## 6. Relevance Filtering Implementation

- **What needs to be built**: AI relevance classifier that filters out noisy feedback (e.g., storage limits, backup sync bugs, billing, generic performance complaints).
- **Module File**: `backend/app/services/relevance.py`
- **Input**: List of `RawObservation` objects (`id`, `user_statement`, `retrieval_scenario`).
- **Output**: Dictionary mapping `id` to `RelevanceResult` (`relevant: bool`, `reason: str`).
- **Connection to Next Component**: Only observations where `relevant == True` are forwarded to the AI Observation Extraction module.

### Criteria Definition:
- **Relevant**: User is attempting to locate a photo/video they remember or believe exists, but face difficulty due to incomplete memory, metadata mismatch, or search limitations.
- **Irrelevant**: Storage full notifications, account login failures, cloud subscription prices, backup app battery drain, feature requests unrelated to retrieval.

### Processing Optimization:
To minimize LLM latency and costs, relevance filtering will evaluate observations in parallel async batches of 10 records using `RelevancePrompt`.

---

## 7. AI/LLM Analysis Workflow

The end-to-end processing pipeline transforms raw evidence through 5 sequential pipeline stages:

```text
[ Raw CSV Input ]
       │
       ▼ (Stage 1: Ingestion & Validation)
[ Validated Raw Observations ]
       │
       ▼ (Stage 2: Async Relevance Filter)
[ Relevant Observations ] ──(Irrelevant)──> Logged & Stored as Irrelevant
       │
       ▼ (Stage 3: LLM Structured Extraction)
[ Structured Observations (14 Fields) ]
       │
       ▼ (Stage 4: Semantic Clustering)
[ Recurring Problem Clusters ]
       │
       ▼ (Stage 5: Opportunity Area Synthesis)
[ Potential Opportunity Areas ] ──> Stored in output/ & Served via API
```

Each stage is completely isolated and idempotent. Processing state is updated in real-time in `output/observations/{analysis_id}_status.json`.

---

## 8. Structured Observation Schema

- **What needs to be built**: Pydantic schema enforcing structured 14-field extraction for every relevant observation.
- **Module File**: `backend/app/models/observation.py`
- **Input**: Relevant raw observation text + LLM prompt.
- **Output**: `StructuredObservation` instance.

### Field Specification

```python
class StructuredObservation(BaseModel):
    id: str                                  # Source observation ID (e.g. "R01")
    source: str                              # Source platform (e.g. "Reddit")
    url: str                                 # Verifiable evidence URL
    retrieval_scenario: str                  # Goal/context of user search
    what_user_remembers: str                 # Memory clues (visual, location, people, context)
    what_user_forgot: str                    # Missing metadata or context ("Not mentioned" if absent)
    search_attempt: str                      # Specific search query or browsing action taken
    search_behavior: str                     # Search pattern (e.g., scrolling, keyword tweaking)
    retrieval_outcome: str                   # Result (e.g., failed, wrong photos, gave up)
    failure_point: str                       # Exact point where search broke down
    workaround: str                          # Alternative action taken ("Not mentioned" if absent)
    problem_category: str                    # Standardized taxonomy category
    evidence_strength: Literal["High", "Medium", "Low"] # Directness of user statement
    analyst_note: str                        # Objective extraction notes (strictly ground-truth)
```

---

## 9. Problem Categorization Logic

- **What needs to be built**: Categorization module that maps user failures to a standardized 9-category taxonomy defined in `problemStatement.md`.
- **Module File**: `backend/app/services/extraction.py` (integrated within Prompt 2 execution).
- **Input**: User statement + extraction context.
- **Output**: Standardized category string assigned to `problem_category`.

### Taxonomy Definition:
1. **Memory expression failure**: User remembers context (e.g., "blue dress at party") but cannot translate it into search terms.
2. **Search understanding failure**: System fails to understand natural language query or context.
3. **Retrieval / indexing failure**: Photo exists and metadata is present, but index fails to return it.
4. **Result relevance failure**: Results returned do not match query intent.
5. **Result evaluation failure**: User cannot verify if target photo is in a large grid of thumbnail results.
6. **Search refinement failure**: User cannot filter or narrow down existing broad search results.
7. **Navigation / browsing failure**: User relies on manual timeline scrolling because search is unhelpful.
8. **Metadata / date / location mismatch**: Photo has wrong timestamp, missing geotag, or incorrect auto-tag.
9. **Other**: Failure mode outside primary taxonomy (must be explicitly explained in `analyst_note`).

---

## 10. Clustering Approach

- **What needs to be built**: Semantic pattern aggregator that groups structured observations sharing similar retrieval failure modes, memory gaps, and search behaviors.
- **Module File**: `backend/app/services/clustering.py`
- **Input**: Array of all `StructuredObservation` objects for the dataset.
- **Output**: Array of `ProblemCluster` objects.
- **Connection to Next Component**: Clusters are passed to the Opportunity Area Generation service.

### Clustering Strategy:
1. **First-Pass Strategy (MVP)**: LLM-based synthesis over the complete set of structured observations (formatted as a condensed JSON list containing `id`, `retrieval_scenario`, `what_user_remembers`, `what_user_forgot`, `failure_point`, `problem_category`).
2. **Semantic Focus**: Grouping is driven by underlying failure points and missing memory elements rather than superficial keyword matching.
3. **Traceability Rule**: Every cluster MUST explicitly reference `supporting_observation_ids`.

---

## 11. Recurring Pattern Identification

- **What needs to be built**: Standardized schema and output formatter for recurring problem clusters.
- **Module File**: `backend/app/models/cluster.py` & `backend/app/services/clustering.py`
- **Input**: Grouped semantic observations.
- **Output**: Validated `ProblemCluster` objects stored in `output/clusters/{analysis_id}.json`.

### Cluster Schema Specification

```python
class ProblemCluster(BaseModel):
    cluster_id: str                          # e.g., "CL-01"
    cluster_name: str                        # Concise title (e.g., "Vague Temporal Memory vs Timestamp Mismatch")
    core_problem: str                        # Root retrieval issue description
    supporting_observation_ids: List[str]    # Array of linked observation IDs (e.g. ["R01", "R05", "GS03"])
    count: int                               # Total supporting observation count
    what_users_remember: str                 # Common memory clues across cluster
    what_is_missing: str                     # Common missing information across cluster
    typical_search_behavior: str             # Dominant search attempt pattern
    failure_point: str                       # Primary point of retrieval failure
    workarounds: str                         # Summary of user workarounds
    evidence_summary: str                    # Summary grounded strictly in supporting evidence
    open_questions_for_interviews: List[str] # 3–4 targeted questions to validate in user interviews
```

---

## 12. Opportunity-Area Generation

- **What needs to be built**: Opportunity synthesis engine that translates evidence-backed problem clusters into research opportunity areas.
- **Module File**: `backend/app/services/opportunities.py`
- **Input**: Array of `ProblemCluster` objects + list of `StructuredObservation` objects.
- **Output**: Array of `OpportunityArea` objects stored in `output/opportunities/{analysis_id}.json`.

### Critical Boundary Constraints:
- **NO Feature Proposals**: Do NOT suggest specific features (e.g., "Build a chat button"). Frame purely as discovery areas (e.g., "Opportunity to improve retrieval when temporal memory is relative rather than exact").
- **NO Ranking**: Do NOT rank or score opportunities by priority.

### Opportunity Area Schema Specification

```python
class OpportunityArea(BaseModel):
    opportunity_id: str                      # e.g., "OPP-01"
    opportunity_name: str                    # Broad problem area title
    user_problem: str                        # Detailed explanation of user friction
    supporting_evidence_ids: List[str]       # Linked observation IDs from underlying clusters
    retrieval_stage: str                     # e.g., Memory Expression, Search Refinement, Browsing
    why_current_workaround_is_insufficient: str # Friction analysis of workarounds
    what_needs_to_be_validated: List[str]    # Validation hypotheses for 5–6 user interviews
```

---

## 13. Evidence Traceability

To satisfy the **Evidence First** architecture principle, the engine establishes an immutable bidirectional traceability chain:

$$\text{Opportunity Area } (\text{OPP-01}) \longrightarrow \text{Problem Cluster } (\text{CL-01}) \longrightarrow \text{Observation ID } (\text{R01}) \longrightarrow \text{Raw CSV Record} \longrightarrow \text{Source URL}$$

### Strict Traceability Guardrails:
1. **Observation ID Persistence**: Every record retains its initial input `id` through all transformation stages.
2. **Strict Grounding Rule**: The LLM is prohibited from inventing details. If a specific detail (e.g., workaround or forgotten element) is not present in the verbatim source statement, the extraction service MUST explicitly set the value to `"Not mentioned"`.
3. **Verification Links**: The React frontend renders direct, clickable hyperlinks to `url` for every observation across tables, cluster views, and opportunity cards.

---

## 14. Backend/FastAPI Implementation

- **What needs to be built**: FastAPI core application server, background job coordinator, CORS config, and JSON state persistence handlers.
- **Module Files**:
  - `backend/app/main.py`: FastAPI initialization, middleware, routes inclusion.
  - `backend/app/config.py`: Environment configuration via `pydantic-settings`.
  - `backend/app/services/llm_client.py`: Configurable API client wrapper supporting retries, timeouts, and selecting ONE active LLM provider based on environment configuration (`LLM_API_KEY`, `LLM_MODEL`).

### Core Dependencies (`requirements.txt`):
```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
python-multipart>=0.0.9
google-genai>=0.1.1
openai>=1.14.0
pytest>=8.0.0
httpx>=0.27.0
```

---

## 15. API Endpoints

The backend exposes RESTful HTTP endpoints for dataset management, pipeline execution, real-time status polling, result retrieval, and data export.

| Method | Endpoint | Request Payload | Response Payload | Description |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/datasets/upload` | `multipart/form-data` (`file: .csv`) | `DatasetUploadResponse` | Uploads custom CSV, validates schema, returns `dataset_id` & preview rows. |
| `GET` | `/api/datasets/preset` | None | `DatasetUploadResponse` | Loads pre-bundled pilot dataset (12 public records) for 1-click reviewer testing. |
| `POST` | `/api/analysis/start` | `{"dataset_id": "uuid"}` | `AnalysisStartResponse` | Triggers async background pipeline execution, returns `analysis_id`. |
| `GET` | `/api/analysis/{analysis_id}/status` | None | `AnalysisStatusResponse` | Returns pipeline stage progress (`stage`, `progress_pct`, `status`). |
| `GET` | `/api/analysis/{analysis_id}/observations` | Optional query filter (`category`, `relevant_only`) | `List[StructuredObservation]` | Fetches extracted 14-field observation records. |
| `GET` | `/api/analysis/{analysis_id}/clusters` | None | `List[ProblemCluster]` | Fetches recurring problem pattern clusters. |
| `GET` | `/api/analysis/{analysis_id}/opportunities` | None | `List[OpportunityArea]` | Fetches potential opportunity areas. |
| `GET` | `/api/analysis/{analysis_id}/export` | Query param (`format: json/csv`) | File download response | Exports full evidence report with complete traceability chain. |

---

## 16. Frontend Screens and Functionality

The frontend is an internal **Product Discovery Research Dashboard** built with React, styled cleanly with CSS variables, offering smooth tabbed navigation across 5 screens:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Google Photos Discovery Engine                       │
│  [1. Upload Dataset] ──> [2. Progress] ──> [3. Observations] ──> ...   │
└────────────────────────────────────────────────────────────────────────┘
```

### Screen Details & Components:

1. **Screen 1 — Dataset Upload & Preset Selection (`FileUpload.jsx`)**:
   - Drag-and-drop custom CSV file selector.
   - **Reviewer Quick-Test Action**: Prominent `"Load Preset Pilot Dataset (12 records)"` button allowing evaluators to launch testing instantly without preparing a file.
   - Live parsing preview table (showing first 5 rows).
   - Validation alert box for missing required headers or invalid rows.
   - Primary `"Start AI Analysis"` action button.

2. **Screen 2 — Analysis Progress (`ProgressStepper.jsx`)**:
   - Visual step-by-step progress indicator:
     - `[✓] Dataset Uploaded & Validated`
     - `[✓] AI Relevance Filtering Completed`
     - `[→] AI Structured Extraction (In Progress...)`
     - `[ ] Semantic Clustering`
     - `[ ] Opportunity Area Synthesis`
   - Real-time polling timer against `/api/analysis/{analysis_id}/status`.

3. **Screen 3 — Structured Observations Table (`ObservationTable.jsx`)**:
   - Interactive data table displaying all 14 extracted fields per record.
   - Filter controls by `Problem Category`, `Source`, and `Evidence Strength`.
   - Clickable source URL links opening external original user evidence in a new tab.
   - Expandable drawer view for full verbatim `user_statement` comparison against AI extraction.

4. **Screen 4 — Problem Clusters View (`ClusterCard.jsx`)**:
   - Card grid rendering each `ProblemCluster`.
   - Displays core problem, user memory state, failure points, and workarounds.
   - Interactive observation badge tags (e.g. `R01`, `GS05`) that highlight or link back to Screen 3 records.
   - Accordion section listing `"Open Questions for User Interviews"`.

5. **Screen 5 — Opportunity Areas View (`OpportunityCard.jsx`)**:
   - Clean summary view displaying discovered opportunity areas.
   - Displays affected retrieval stage and why existing workarounds fail.
   - Direct evidence traceability badges linking back to supporting observation IDs.
   - Export toolbar with `"Export JSON"` and `"Export CSV"` actions.

---

## 17. LLM Prompt Structure

Prompt templates are isolated in `backend/app/prompts/` and strictly enforce JSON output parsing via system instructions.

### Prompt 1: Relevance Filter (`relevance_prompt.py`)
```text
SYSTEM: You are a senior product research assistant on Google Photos Core Experience team.
TASK: Determine if the user statement describes a photo/video retrieval scenario where the user remembers a photo but faces difficulty finding it.

RELEVANT CRITERIA:
- User is searching for a specific photo/video they believe exists in their library.
- User relies on vague/incomplete memory (location, date, people, visual details).
- User experiences friction or search failure.

IRRELEVANT CRITERIA:
- Cloud backup sync errors, storage quota/billing, login/account issues, general app speed.

INPUT:
ID: {id}
Statement: "{user_statement}"
Scenario: "{retrieval_scenario}"

OUTPUT FORMAT (JSON ONLY):
{
  "relevant": true|false,
  "reason": "Short 1-sentence explanation"
}
```

### Prompt 2: Structured Observation Extraction (`extraction_prompt.py`)
```text
SYSTEM: You are an expert qualitative research analyst. Convert the raw user statement into structured research fields.

STRICT GROUNDING RULES:
1. Extract ONLY facts present in the text.
2. If a field is not explicitly mentioned or clearly implied, output EXACTLY "Not mentioned". Do NOT assume or invent details.
3. Categorize into EXACTLY ONE of these categories:
   ["Memory expression failure", "Search understanding failure", "Retrieval / indexing failure", "Result relevance failure", "Result evaluation failure", "Search refinement failure", "Navigation / browsing failure", "Metadata / date / location mismatch", "Other"]

INPUT:
ID: {id}
Source: {source}
URL: {url}
Statement: "{user_statement}"
Scenario: "{retrieval_scenario}"

OUTPUT FORMAT (JSON ONLY):
{
  "id": "{id}",
  "source": "{source}",
  "url": "{url}",
  "retrieval_scenario": "...",
  "what_user_remembers": "...",
  "what_user_forgot": "...",
  "search_attempt": "...",
  "search_behavior": "...",
  "retrieval_outcome": "...",
  "failure_point": "...",
  "workaround": "...",
  "problem_category": "...",
  "evidence_strength": "High|Medium|Low",
  "analyst_note": "..."
}
```

### Prompt 3: Semantic Clustering (`clustering_prompt.py`)
```text
SYSTEM: You are a Principal PM analyzing qualitative photo retrieval observations.
TASK: Group the provided structured observations into 3-6 distinct, recurring problem clusters based on shared retrieval failure modes and memory gaps.

RULES:
- Ground every cluster strictly in the provided observation IDs.
- Do NOT rank clusters by importance. Frequency indicates evidence count, not automatic priority.

INPUT OBSERVATIONS:
{structured_observations_json}

OUTPUT FORMAT (JSON ONLY):
[
  {
    "cluster_id": "CL-01",
    "cluster_name": "...",
    "core_problem": "...",
    "supporting_observation_ids": ["R01", "R04"],
    "count": 2,
    "what_users_remember": "...",
    "what_is_missing": "...",
    "typical_search_behavior": "...",
    "failure_point": "...",
    "workarounds": "...",
    "evidence_summary": "...",
    "open_questions_for_interviews": ["Question 1", "Question 2"]
  }
]
```

### Prompt 4: Opportunity Area Synthesis (`opportunity_prompt.py`)
```text
SYSTEM: Synthesize recurring problem clusters into broad research opportunity areas for user interview validation.

STRICT BOUNDARY RULES:
- Do NOT propose specific product features or UI solutions (e.g. do NOT say "Build an AI chatbot").
- Do NOT rank or score opportunities.
- Frame purely as problem/research discovery spaces.

INPUT CLUSTERS:
{clusters_json}

OUTPUT FORMAT (JSON ONLY):
[
  {
    "opportunity_id": "OPP-01",
    "opportunity_name": "...",
    "user_problem": "...",
    "supporting_evidence_ids": ["R01", "R04"],
    "retrieval_stage": "...",
    "why_current_workaround_is_insufficient": "...",
    "what_needs_to_be_validated": ["Hypothesis 1", "Hypothesis 2"]
  }
]
```

---

## 18. Error Handling

| Scenario | Potential Failure | Handling & Recovery Strategy |
| :--- | :--- | :--- |
| **CSV Validation** | Missing mandatory headers or malformed formatting. | Reject upload with clear HTTP 400 JSON detailing line numbers and missing field names. |
| **LLM Rate Limit / Timeout** | HTTP 429 or 504 from LLM API provider. | Exponential backoff retry wrapper in `llm_client.py` (max 3 retries, base delay 2s). |
| **Invalid LLM JSON Response** | Model returns non-JSON string or markdown code fence block. | Custom JSON parser stripping code fences + Pydantic validation fallback. If retry fails, mark single record as `"extraction_failed"` without aborting pipeline. |
| **Partial Analysis Failure** | 2 out of 50 observations fail extraction. | Pipeline completes for 48 valid observations; failed records are logged in state JSON for manual review. |
| **Pipeline Interruption** | Server crash mid-analysis. | Analysis status stored on disk (`output/observations/{analysis_id}_status.json`) allowing resumable pipeline execution. |

---

## 19. Testing Strategy

1. **Backend Unit Tests (`pytest tests/unit/`)**:
   - `test_ingestion.py`: Verify CSV parsing, schema validation, and deduplication logic.
   - `test_relevance.py`: Test classification logic against known relevant/irrelevant text fixtures using mocked LLM responses.
   - `test_schemas.py`: Verify strict Pydantic model validation on 14-field extraction schema.

2. **Integration Tests (`pytest tests/integration/`)**:
   - `test_api_routes.py`: FastAPI `TestClient` verification for `/upload`, `/start`, `/status`, and result endpoints.
   - `test_pipeline.py`: End-to-end processing test using `sample_observations.csv` with a mocked LLM service layer.

3. **Frontend Component Tests**:
   - Render tests for `FileUpload.jsx`, `ObservationTable.jsx`, and `ProgressStepper.jsx`.

---

## 20. Pilot Dataset Implementation

To validate the end-to-end pipeline before scaling, a pilot dataset (`data/sample_observations.csv`) containing **12 realistic public user observations** will be created:

### Sample Pilot Data Preview

```csv
id,source,url,user_statement,retrieval_scenario
R01,Reddit,https://reddit.com/r/googlephotos/comments/ex1,"I remember taking a picture of a wine label in Italy 3 years ago but don't know the exact city or month.",Find wine label photo from Italy trip
R02,Reddit,https://reddit.com/r/googlephotos/comments/ex2,"Searching 'blue car' shows every car except my old Honda Civic which was parked near water.",Retrieve photo of old blue car near water
GP01,PlayStore,https://play.google.com/store/apps/details?id=com.google.android.apps.photos,"App keeps asking me to buy Google One storage every time I open it!",Storage quota complaint
GS01,GoogleSupport,https://support.google.com/photos/thread/101,"I know I have a photo of my dog wearing a Santa hat from Christmas 2019 but search only brings up 2022 photos.",Retrieve older dog holiday photo
```

The pilot dataset validates:
- Filtering out irrelevant records (`GP01` correctly flagged as `relevant: false`).
- Extraction of all 14 fields with strict `"Not mentioned"` compliance.
- Synthesis of at least 2 distinct problem clusters and 2 opportunity areas.

---

## 21. Scaling from Pilot to 50–100+ Observations

To scale seamlessly from the pilot dataset to 50–100+ public user observations without hitting API rate limits or token context windows:

1. **Async Batch Processing**: Observations are processed in concurrent chunks of 10 records using Python's `asyncio.gather` with an `asyncio.Semaphore(5)` rate-limiter.
2. **Chunked Semantic Clustering**: When observation count exceeds 50, clustering uses a two-pass approach:
   - *Pass 1*: Group observations by `problem_category`.
   - *Pass 2*: Perform LLM semantic synthesis across category groups to form global cross-category clusters.
3. **Local File Caching**: Every stage output is immediately written to disk (`output/observations/`, `output/clusters/`), ensuring zero redundant API calls if a downstream stage needs re-execution.

---

## 22. Research Quality Controls

1. **Strict Evidence Grounding**: Every insight in a cluster or opportunity area must explicitly map to underlying `supporting_observation_ids`.
2. **"Not Mentioned" Rule**: The LLM is strictly penalized via system instructions for inventing user details not present in the raw text.
3. **Deduplication**: Duplicate user posts across platforms are deduplicated prior to relevance analysis.
4. **Source Diversity Tracking**: The dashboard tracks observation count distribution across platforms (Reddit vs. Support vs. Play Store) to identify source bias.
5. **Human Validation Readiness**: All generated open questions and opportunity areas are structured specifically to serve as input for subsequent **5–6 qualitative user interviews**.

---

## 23. Definition of Done

Part 1 — AI-Powered Discovery Engine is considered **Done** when:

```text
A raw CSV dataset containing public user observations
                       ↓
          Can be uploaded via React UI
                       ↓
   Irrelevant feedback is filtered out by AI relevance layer
                       ↓
   Each relevant observation is structured into 14 normalized fields
                       ↓
Observations are aggregated into evidence-backed recurring problem clusters
                       ↓
Potential research opportunity areas are generated without proposing product solutions
                       ↓
 Every insight remains fully traceable to original source URLs & verbatim quotes
                       ↓
 Results can be browsed interactively on the dashboard and exported as JSON/CSV
```

---

## 24. Step-by-Step Implementation Order

The development execution will proceed strictly in the following 4 sequential phases:

### Phase 1 — Foundation & Data Ingestion
- Create project directory layout (`data/`, `backend/`, `frontend/`, `output/`).
- Initialize Python environment, `requirements.txt`, and `.env.example`.
- Setup FastAPI base app (`main.py`, `config.py`).
- Create `data/sample_observations.csv` (12 pilot records).
- Implement `backend/app/services/ingestion.py` and Pydantic models in `backend/app/models/dataset.py`.
- Build and unit test dataset endpoints (`POST /api/datasets/upload` and `GET /api/datasets/preset`).

### Phase 2 — AI Discovery Pipeline
- Implement `llm_client.py` wrapper selecting active LLM provider based on environment config.
- Implement `relevance.py` and Prompt 1 (Relevance filtering service).
- Implement `extraction.py` with 14-field Pydantic schema and Prompt 2 (Structured extraction service).
- Implement `clustering.py` and Prompt 3 (Semantic clustering service).
- Implement `opportunities.py` and Prompt 4 (Opportunity area synthesis service).
- Implement API routers in `backend/app/routes/` (`analysis_routes.py`).
- Implement file-based JSON persistence in `output/` for status, observations, clusters, and opportunities.
- Verify end-to-end backend AI pipeline execution using `pytest` and `sample_observations.csv`.

### Phase 3 — Research Dashboard & Validation
- Initialize Vite + React project in `frontend/`.
- Build UI components (`FileUpload`, `ProgressStepper`, `ObservationTable`, `ClusterCard`, `OpportunityCard`).
- Connect React UI to FastAPI backend via API service (`src/services/api.js`).
- Run full pilot workflow end-to-end via React UI.
- Verify evidence traceability links and export functionality.
- Execute scaled test with 50+ observations to ensure batching stability.

### Phase 4 — Deployment & Reviewer Testing
- Containerize / configure backend web service on Render / Railway with pre-configured API keys.
- Deploy React frontend to Vercel / Render Static Site.
- Perform end-to-end smoke test on the live deployment URL.
- Validate reviewer quick-test workflow ("Load Preset Pilot Dataset" 1-click evaluation).

---

## 25. Deployment Architecture & Public Reviewer Testability

To satisfy submission requirements for a publicly accessible, testable MVP prototype, the engine will be deployed as a live cloud application:

### Public Hosting Setup:
1. **Frontend Hosting**: Deployed to Vercel or Render Static Site, exposing a clean HTTPS live application link for reviewers.
2. **Backend Hosting**: Deployed as a Python 3.11 web service on Render / Railway, running Uvicorn + FastAPI with CORS enabled for the frontend origin.
3. **Environment Security**: The `LLM_API_KEY` and `LLM_MODEL` are injected securely into the backend environment settings. Evaluators do NOT need to supply their own API keys to test the workflow.

### Reviewer End-to-End Testability Flow:
Evaluators and reviewers can complete the full discovery workflow in under 2 minutes:

```text
[ Open Public Application URL ]
               │
               ▼
[ Click "Load Preset Pilot Dataset (12 records)" OR Upload custom CSV ]
               │
               ▼
[ Click "Start AI Analysis" ]
               │
               ▼
[ Watch Real-Time Stage Progress Bar ]
   ├── Stage 1: Relevance Filtering (Irrelevant records like storage complaints separated)
   ├── Stage 2: 14-Field Structured Extraction (View memory, failure points, workarounds)
   ├── Stage 3: Semantic Problem Clustering (View recurring problem patterns)
   └── Stage 4: Opportunity Area Synthesis (View broad research opportunity spaces)
               │
               ▼
[ Click any Source URL link or Observation ID badge to verify Evidence Traceability ]
               │
               ▼
[ Export Complete Analysis Report as JSON or CSV ]
```

### Dynamic MVP Verification:
The MVP is confirmed **NOT** to be a static dashboard, CLI script, or standalone backend API. It is an interactive, full-stack AI workflow system where uploading or selecting a dataset dynamically triggers live AI processing, state management, structured analysis, and evidence-backed synthesis.

