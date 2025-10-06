# Proposal: Structured Metadata Backbone for WorkDrive

**Goal:** Build a reliable, auditable pipeline that inventories WorkDrive documents, extracts text, classifies with heuristics + optional LLM, enables manual review, and writes normalized metadata back into WorkDrive **Data Templates** (so the metadata becomes searchable in the native UI and ready for future RAG).

**Why this design works**
- **Auth-code + refresh token** → unattended rotation, fewer surprises vs client-credentials
- **SQLite** → simple, portable audit trail; upgrade to Postgres later without code churn
- **Incremental crawl** → avoids rate limits; respects paging
- **Heuristic-first** → cheap wins; LLM only for uncertain cases
- **Single source of truth** → corrections synced to WorkDrive Data Templates
