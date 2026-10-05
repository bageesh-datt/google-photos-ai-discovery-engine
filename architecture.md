# Google Photos AI-Powered Discovery Engine — Architecture

## 1. Purpose

This document defines the technical and functional architecture for **Part 1 — AI-Powered Discovery Engine** of the NextLeap Graduation Project.

The engine is an internal Product Discovery / Research system.

Its purpose is to transform public user feedback and conversations about Google Photos photo retrieval into:

**Raw User Evidence → Structured Retrieval Observations → Recurring Problem Patterns → Potential Opportunity Areas**

The engine is for **problem discovery**, not for building the final Google Photos photo-retrieval product.

---

# 2. Architecture Principles

The system should follow these principles:

1. **Evidence first**
   - Every important insight must be traceable to an original user observation and source URL.

2. **AI-assisted, not AI-invented**
   - AI should structure and analyze evidence.
   - AI must not invent user behavior or prevalence.

3. **Problem before solution**
   - Part 1 should identify retrieval problems and opportunity areas.
   - Product features/solutions are outside the scope of this stage.

4. **Structured analysis**
   - Free-form user conversations should be converted into consistent fields.

5. **Scalable workflow**
   - The same pipeline should work for a small pilot dataset and later for 50–100+ relevant observations.

6. **Human validation**
   - AI findings are hypotheses/starting points and must later be validated through 5–6 user interviews.

---

# 3. High-Level System Architecture

```text
┌──────────────────────────────────────────────┐
│              PUBLIC USER EVIDENCE            │
│                                              │
│ Reddit | Google Photos Community | Reviews   │
│ Other relevant public conversations          │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              DATA INGESTION                  │
│                                              │
│ CSV / structured input                       │
│ Source + URL + user statement + scenario     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          RELEVANCE FILTERING                 │
│                                              │
│ Is this about photo/video retrieval?         │
│ Is the user trying to find a known/remembered│
│ photo with incomplete information?           │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│               AI ANALYSIS                   │
│                                              │
│ Memory clues                                │
│ Missing information                         │
│ Search behavior                             │
│ Retrieval outcome                           │
│ Failure point                               │
│ Workaround                                  │
│ Problem category                            │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          STRUCTURED OBSERVATIONS             │
│                                              │
│ One normalized record per user observation   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│              CLUSTERING                      │
│                                              │
│ Group observations with similar retrieval    │
│ problems and behaviors                       │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          RECURRING PATTERNS                  │
│                                              │
│ Evidence-backed problem patterns             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          OPPORTUNITY AREAS                   │
│                                              │
│ Problems requiring deeper user validation    │
└──────────────────────────────────────────────┘
```

---

# 4. Proposed Technology Stack

## Frontend

**React**

Responsibilities:

- Upload dataset
- Start analysis
- Display processing status
- Display analyzed observations
- Display clusters
- Display opportunity areas
- Show source/evidence links
- Export results

The frontend is an internal research dashboard, not the final Google Photos user product.

---

## Backend

**Python + FastAPI**

Responsibilities:

- Receive CSV uploads
- Validate input schema
- Run relevance filtering
- Send observations to the LLM
- Normalize AI responses
- Store analysis results
- Run clustering
- Generate recurring patterns
- Generate opportunity areas
- Provide APIs to the frontend

---

## AI / LLM Layer

Use an LLM through an API.

The model should be configurable through an environment variable.

Example:

```text
LLM_API_KEY
LLM_MODEL
```

Do not hard-code API keys in source code.

The LLM is responsible for semantic analysis, structured extraction, clustering support, and opportunity synthesis.

---

## Storage

For the initial version:

**CSV + JSON local storage**

Use CSV for:

- Raw observations
- Import/export

Use JSON for:

- AI analysis results
- Cluster results
- Opportunity results

A database can be introduced later if the dataset or application requires it.

---

# 5. Data Input Schema

The minimum input CSV should contain:

```text
id
source
url
user_statement
retrieval_scenario
```

Example:

```csv
id,source,url,user_statement,retrieval_scenario
R01,Reddit,https://example.com,"I remember a photo from my Goa trip but don't remember the date","Find old Goa trip photo"
```

---

# 6. Relevance Filtering

Before expensive AI analysis, the system should determine whether an observation is relevant.

## Relevant

The observation should generally involve:

- A photo/video the user wants to retrieve
- A photo/video the user remembers or believes exists
- Incomplete memory, metadata, or search clues
- Difficulty finding the photo/video

## Irrelevant examples

Do not treat these as core retrieval evidence:

- General storage complaints
- Backup problems that do not affect retrieval
- Pricing complaints
- General performance complaints
- Account/login issues
- Unrelated Google Photos features

The filtering stage should return:

```text
relevant: true / false
reason: ...
```

---

# 7. AI Observation Extraction

For every relevant observation, the LLM should extract:

```text
id
source
url
retrieval_scenario
what_user_remembers
what_user_forgot
search_attempt
search_behavior
retrieval_outcome
failure_point
workaround
problem_category
evidence_strength
analyst_note
```

## Missing information rule

If the source does not mention something:

```text
Not mentioned
```

Do not infer it.

---

# 8. Problem Categories

Initial taxonomy:

```text
1. Memory expression failure

2. Search understanding failure

3. Retrieval / indexing failure

4. Result relevance failure

5. Result evaluation failure

6. Search refinement failure

7. Navigation / browsing failure

8. Metadata / date / location mismatch

9. Other
```

The taxonomy can be refined if actual evidence shows that another category better explains recurring behavior.

---

# 9. Evidence Traceability

Every structured observation must retain:

```text
Observation ID
Source
Original URL
```

Cluster results must retain:

```text
Supporting observation IDs
```

Opportunity areas must retain:

```text
Supporting observation IDs
```

Therefore the research chain should be:

```text
Opportunity
    ↓
Cluster
    ↓
Observation IDs
    ↓
Original user evidence
    ↓
Source URL
```

This prevents unsupported AI-generated conclusions.

---

# 10. Clustering Layer

After individual observations are structured, similar observations should be grouped.

The clustering layer should consider semantic similarity across:

- Retrieval scenario
- What users remember
- What users forget
- Search behavior
- Failure point
- Problem category

For the first implementation, clustering can use an LLM-based synthesis over structured observations.

A future version can add embeddings + vector similarity + algorithmic clustering if needed.

---

# 11. Cluster Output Schema

Each cluster should contain:

```text
cluster_name
core_problem
supporting_observation_ids
count
what_users_remember
what_is_missing
typical_search_behavior
failure_point
workarounds
evidence_summary
open_questions_for_interviews
```

Important:

**Cluster frequency is evidence of recurrence, not automatically importance.**

Do not rank clusters in Part 1.

---

# 12. Opportunity Area Layer

The opportunity layer converts recurring patterns into areas that deserve further investigation.

Each opportunity should contain:

```text
opportunity_name
user_problem
supporting_evidence_ids
retrieval_stage
why_current_workaround_is_insufficient
what_needs_to_be_validated
```

The opportunity layer must not directly generate a product feature.

Example:

```text
Observed pattern:
Users remember contextual details but lack precise metadata.

Potential opportunity:
Improve retrieval from contextual memory.

NOT:
Build a conversational AI search button.
```

The latter is a solution and belongs to a later stage.

---

# 13. End-to-End Processing Pipeline

```text
1. Upload CSV
        ↓
2. Validate schema
        ↓
3. Deduplicate observations
        ↓
4. Relevance filtering
        ↓
5. AI structured extraction
        ↓
6. Store structured observations
        ↓
7. Cluster observations
        ↓
8. Identify recurring patterns
        ↓
9. Generate opportunity areas
        ↓
10. Display evidence-backed results
        ↓
11. Export JSON / CSV
```

---

# 14. API Design

Suggested FastAPI endpoints:

```text
POST /api/datasets/upload
```

Upload a CSV dataset.

```text
POST /api/analysis/start
```

Start the AI analysis pipeline.

```text
GET /api/analysis/{analysis_id}/status
```

Return processing status.

```text
GET /api/analysis/{analysis_id}/observations
```

Return structured observations.

```text
GET /api/analysis/{analysis_id}/clusters
```

Return recurring problem clusters.

```text
GET /api/analysis/{analysis_id}/opportunities
```

Return potential opportunity areas.

```text
GET /api/analysis/{analysis_id}/export
```

Export analysis results.

---

# 15. Frontend Screens

## Screen 1 — Dataset Upload

Components:

- CSV upload
- Dataset preview
- Number of observations
- Start Analysis button

---

## Screen 2 — Analysis Progress

Show stages:

```text
✓ Dataset validated
✓ Relevant observations identified
→ AI analysis
○ Clustering
○ Opportunity synthesis
```

---

## Screen 3 — Observation Analysis

Display a table:

```text
ID
Source
Scenario
Remembered
Forgotten
Search
Failure
Category
Evidence
```

Allow the user to open the source URL.

---

## Screen 4 — Problem Clusters

For each cluster show:

- Cluster name
- Observation count
- Core problem
- Failure point
- Supporting observation IDs
- Evidence summary

---

## Screen 5 — Opportunity Areas

Show:

- Opportunity name
- User problem
- Evidence
- Retrieval stage
- Validation questions

No solution ranking.

---

# 16. AI Prompt Architecture

Use separate prompts for separate research tasks.

## Prompt 1 — Relevance

Determine whether the observation belongs to the vague-photo-retrieval problem space.

## Prompt 2 — Observation Extraction

Convert a relevant user conversation into structured fields.

## Prompt 3 — Clustering

Identify recurring patterns from structured observations.

## Prompt 4 — Opportunity Synthesis

Identify evidence-backed areas for deeper research.

Keeping these tasks separate makes the pipeline easier to debug and evaluate.

---

# 17. Error Handling

The system should handle:

- Invalid CSV format
- Missing required columns
- Empty dataset
- Duplicate observations
- LLM API failure
- LLM timeout
- Invalid JSON response
- Rate limits
- Partial analysis failure

A failed observation should not cause the entire dataset to fail.

Store an analysis status such as:

```text
pending
processing
completed
failed
```

For individual records:

```text
success
failed
```

---

# 18. Scale Strategy

The pilot can begin with a small dataset.

After validating the workflow, scale toward approximately:

**50–100+ relevant observations**

The architecture should avoid sending the entire dataset to the LLM in one request.

Instead:

```text
Dataset
   ↓
Batches
   ↓
Individual / batch extraction
   ↓
Structured JSON
   ↓
Aggregate analysis
```

This reduces token limits and makes failures easier to retry.

---

# 19. Research Quality Controls

The system should include checks for:

### Grounding

Every insight should point back to observation IDs.

### Missing data

Use "Not mentioned" instead of assumptions.

### Duplicate evidence

Avoid counting the same observation multiple times.

### Source diversity

Track which source each observation came from.

### Hypothesis labeling

Clearly distinguish:

```text
Observed behavior
Interpretation
Hypothesis
```

### Human validation

The final discovery output is not the final product decision.

The strongest patterns should be taken into the required **5–6 user interviews** for validation.

---

# 20. Folder Structure

Recommended implementation:

```text
google-photos-discovery-engine/
│
├── problemStatement.md
├── architecture.md
├── README.md
├── .env.example
├── requirements.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample_observations.csv
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── models/
│       ├── schemas/
│       ├── routes/
│       ├── services/
│       │   ├── ingestion.py
│       │   ├── relevance.py
│       │   ├── extraction.py
│       │   ├── clustering.py
│       │   └── opportunities.py
│       └── prompts/
│
├── frontend/
│   └── ...
│
└── output/
    ├── observations/
    ├── clusters/
    └── opportunities/
```

---

# 21. MVP Boundary for Part 1

The first implementation should be intentionally focused.

### Must have

- CSV upload/import
- Relevant-observation filtering
- LLM structured extraction
- Evidence traceability
- Problem categories
- Clustering
- Opportunity-area generation
- Dashboard/results
- Export

### Not required yet

- Google Photos API integration
- Real user photo access
- Actual photo retrieval
- Consumer-facing chatbot
- Final product UI
- Production-scale cloud deployment

Those belong to later stages or are outside Part 1.

---

# 22. Definition of Done

Part 1 is considered technically complete when:

```text
A CSV containing public user observations
              ↓
        can be uploaded
              ↓
Relevant retrieval observations are identified
              ↓
Each relevant observation is structured by AI
              ↓
Observations can be grouped into recurring problems
              ↓
Evidence-backed opportunity areas are generated
              ↓
Every important insight can be traced to source observations
              ↓
Results can be viewed/exported
```

The output should help answer:

> **What are the recurring ways users fail to retrieve vaguely remembered photos, and what evidence supports those patterns?**

It should NOT answer:

> **What feature should Google Photos build?**

That decision comes only after further research and validation.
