# NextLeap Graduation Project — Problem Statement

## Project Context

I am working on the NextLeap Product Management Graduation Project.

### Role

Assume the role of a Product Manager on the **Core Experience team at Google Photos**.

---

# Business Problem

The business goal is to increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they start searching.

The problem is specifically about **photo retrieval when the user's memory is incomplete or vague**.

Examples of vague memories:

- A user remembers a photo from a trip but does not remember the exact date or location.
- A user remembers seeing a photo previously but cannot remember where/how they found it.
- A user remembers the context, people, object, or event in a photo but cannot provide precise searchable metadata.

The goal is NOT to assume that the existing search experience is broken.

Instead, we need to discover **where and why retrieval fails for users with vague memories**.

---

# Part 1 — Build an AI-Powered Discovery Engine

Before proposing any product solution, build an AI-powered system that analyzes user feedback and conversations about photo retrieval **at scale**.

The system should analyze public user conversations/feedback from sources such as:

- Google Play Store reviews
- App Store reviews
- Reddit
- Google Photos Community / Support
- Social media
- YouTube comments
- Forums

The system does not need to use every source. The selected sources should provide relevant evidence about photo-retrieval problems.

---

# Discovery Engine Objective

The Discovery Engine should help answer:

> **When users remember that a photo exists but cannot precisely describe it, what prevents them from successfully retrieving it?**

For each relevant user observation, the system should identify:

1. What the user is trying to retrieve
2. What the user remembers
3. What the user does not remember / has forgotten
4. How the user attempts to search
5. What happens during the search
6. Where retrieval fails
7. What workaround the user uses
8. What type of retrieval problem is occurring

The system should then group similar observations into recurring problem patterns.

---

# Required Analysis Categories

The Discovery Engine should be able to identify, where supported by evidence:

- Memory expression failure
- Search understanding failure
- Retrieval / indexing failure
- Result relevance failure
- Result evaluation failure
- Search refinement failure
- Navigation / browsing failure
- Metadata / date / location mismatch
- Other retrieval-related problems

These categories are an initial framework and may be refined if the evidence suggests better categories.

---

# AI Analysis Requirements

For each user observation, extract structured information such as:

- Observation ID
- Source
- Source URL
- Retrieval scenario
- What user remembers
- What user forgot
- Search attempt
- Search behavior
- Retrieval outcome
- Failure point
- Existing workaround
- Problem category
- Evidence strength
- Analyst notes

Important research rules:

- Do not invent information that is not present in the source.
- If information is not mentioned, use **"Not mentioned"**.
- Clearly separate observed user behavior from interpretation.
- Preserve traceability to the original source.
- Do not treat one user's complaint as proof that the problem is widespread.
- Do not use sentiment analysis as the primary research output.
- Do not propose product features during the discovery stage.
- Do not rank opportunities at this stage.

---

# Pattern / Clustering Analysis

After individual observations are analyzed, the system should identify recurring patterns.

For each cluster, capture:

- Cluster name
- Core user problem
- Supporting observation IDs
- Number of observations
- What users remember
- What information is missing
- Typical search behavior
- Retrieval failure point
- Existing workarounds
- Evidence summary
- Questions that should be validated through user interviews

The clustering should be evidence-driven.

Do not assume that the most frequently mentioned issue is automatically the most important opportunity.

---

# Opportunity Areas

After recurring patterns are identified, the system should generate **potential opportunity areas** based only on the evidence.

For each opportunity area, capture:

- Opportunity name
- User problem
- Supporting evidence IDs
- Retrieval stage affected
- Why the current workaround may be insufficient
- What needs to be validated through user interviews

At this stage:

- Do NOT propose a specific product feature.
- Do NOT design the final solution.
- Do NOT rank opportunities.

The purpose is to identify areas that require deeper user research.

---

# Expected Discovery Flow

The intended workflow is:

Public User Feedback / Conversations
        ↓
Data Collection
        ↓
Relevant Retrieval Conversations
        ↓
AI Relevance Filtering
        ↓
AI Structured Extraction
        ↓
Memory + Missing Information
        ↓
Search Behavior
        ↓
Retrieval Failure Point
        ↓
Existing Workaround
        ↓
Problem Categorization
        ↓
AI Clustering
        ↓
Recurring Retrieval Patterns
        ↓
Potential Opportunity Areas
        ↓
5–6 User Interviews for Validation

---

# Scale

The Discovery Engine should be designed to work beyond a handful of examples.

For the pilot, use a small sample to validate the workflow.

After the workflow is validated, scale the dataset to a substantially larger set of relevant observations (target approximately 50–100+ observations, depending on source availability and relevance).

The objective is to demonstrate that AI can help analyze user feedback and conversations at scale.

---

# Part 1 Deliverables

The Part 1 output should include:

1. A working AI-powered Discovery Engine / workflow
2. Data collection/input structure
3. A dataset of relevant public user observations
4. AI-generated structured analysis for each observation
5. Retrieval problem taxonomy
6. Recurring problem clusters
7. Potential opportunity areas
8. Traceability from insights back to source observations
9. Documentation explaining the workflow and methodology

---

# Important Project Boundary

This is **ONLY Part 1**.

Do NOT build the final Google Photos photo-retrieval product yet.

The later project stages will use the Discovery Engine findings for:

- Business metric decomposition
- 5–6 user interviews
- Problem definition
- AI-native MVP
- Testing with 3+ users

Therefore, the Discovery Engine should focus on **discovering and structuring the problem**, not solving it.

---

# Success Criteria for Part 1

Part 1 is successful if the system can take a collection of real public user conversations and systematically transform them into:

**Raw User Evidence**
→ **Structured Retrieval Observations**
→ **Recurring Problem Patterns**
→ **Potential Opportunity Areas**

while keeping every important insight traceable to actual evidence.

