# Question: How is the SourcingAgent implemented?

The SourcingAgent searches the internal candidate database, job boards, and sub-vendors. Key decisions:

**Implementation decisions:**
1. **Internal DB search** — How to search 50K+ candidates efficiently? Structured filters (location, experience, visa, salary) + vector skill search
2. **Hybrid search** — Combine vector similarity (pgvector) with keyword/structured filters. What's the weighting?
3. **Job board monitoring** — RSS/API polling? How often? Which job boards?
4. **Sub-vendor intake** — Receive and process candidate profiles from sub-vendors (out of MVP scope per PRD, but interface should be defined)
5. **Job details lookup** — Fetch full job requisition details for context-aware sourcing
6. **Result format** — What metadata does the SourcingAgent return to the Orchestrator?
7. **Tenant scoping** — All queries must be tenant-scoped (existing TenantMiddleware)
8. **Caching** — Should job board results be cached? For how long?

**Existing data:**
- `candidates` table with tenant scoping
- `candidate_skills` table with skill embeddings
- `client_contacts` table with job requirements

Resolve by implementing the SourcingAgent tools, the hybrid search query, and the job board polling infrastructure.

---

## Resolution

**Date:** 2026-07-26

**File updated:** `services/agent_orchestrator/sourcing_agent.py` (replaced placeholder with full implementation)

**Implementation decisions:**

1. **Internal DB search:** SQLAlchemy async queries with tenant scoping (`organization_id`). Structured search uses ILIKE on title/location/employer fields. Full-text search uses PostgreSQL `tsvector` + `plainto_tsquery`. Vector search uses pgvector cosine similarity (MVP uses skill name matching as fallback).

2. **Hybrid search:** Reciprocal Rank Fusion (RRF) with constant 60. Three parallel signals:
   - Structured keyword match (title, location, employer)
   - Full-text search (tsvector on profile fields)
   - Vector similarity (pgvector on skill embeddings)
   RRF combines without needing score normalization.

3. **Job board monitoring:** Out of scope for MVP (per PRD Phase 4+). Interface defined but not implemented.

4. **Sub-vendor intake:** Out of scope for MVP (per PRD). Interface defined but not implemented.

5. **Job details lookup:** Queries `client_contacts` table. Returns title, client, required_skills, location, experience, visa requirements.

6. **Result format:** Candidate dicts with id, name, title, location, employer, visa_status, notice_period, skills (list), fit_score (0-1), strengths (list), gaps (list).

7. **Tenant scoping:** All queries filtered by `organization_id`. Consistent with existing `TenantMiddleware` pattern.

8. **Caching:** Not implemented for MVP. Candidate data changes infrequently; cache can be added in Phase 3+.

9. **Keyword extraction:** `_extract_keywords()` filters stop words and returns meaningful tokens for structured search.

**Remaining work:**
- Vector search needs actual pgvector embedding column on `candidate_skills` table (currently uses ILIKE fallback)
- Structured search uses simplified SQL (production should use proper SQLAlchemy constructs)
- Job board polling infrastructure not implemented (out of MVP scope)
- Sub-vendor intake interface not implemented (out of MVP scope)
