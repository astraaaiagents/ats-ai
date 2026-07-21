# Second Opinion Review: AI-Native Features Implementation Specification

**Reviewer:** MIMO v2.5  
**Date:** 2026-07-21  
**Spec Under Review:** `docs/superpowers/specs/2026-07-21-ai-native-features-spec.md`  
**Verdict:** REVISIONS NEEDED — Strong architectural foundation with gaps in failure handling, multi-tenancy, and LLM-specific edge cases  

---

## Summary

The spec demonstrates solid understanding of AI middleware patterns. The PII shield architecture is well-designed, the prompt contracts are clear and structured, and the integration points are explicit. However, the spec has material gaps in three areas: (1) LLM failure modes and fallback strategies are underspecified, (2) multi-tenancy and data residency are not addressed despite being core requirements, and (3) several features make optimistic assumptions about LLM behavior that will break in production.

---

## Strengths

1. **PII shield architecture is excellent.** The ephemeral token map, NER + regex layered approach, and side-by-side verification UI demonstrate real-world compliance thinking. The Scunthorpe problem mitigation shows attention to edge cases.

2. **Prompt contracts are well-structured.** Each prompt specifies input format, output schema, and constraints. The anonymization instruction ("Do NOT use the candidate's name") shows understanding of how PII flows through the system.

3. **Error state tables are thorough.** Most features include error scenarios with specific behaviors, not just "handle gracefully." The manual review queue for low-confidence redactions is a practical compliance pattern.

4. **Audit logging is consistently integrated.** Every feature references the audit log with specific data points to capture. The redaction audit log's "no PII values stored" constraint is correct.

5. **Rate limits are defined per-feature.** This prevents runaway costs and shows production thinking.

---

## Critical Issues

### 1. Multi-Tenancy Not Addressed in AI Service Layer

The architecture overview says "AI Service Layer is a dedicated microservice with its own database, queue, and API" but never explains:
- How does the AI service know which tenant is making the request?
- Are LLM calls routed through a single endpoint or per-region endpoints?
- How does the audit log associate AI calls with the correct tenant?
- How does the PII shield handle tenant-specific redaction rules (e.g., EU tenants may have stricter rules than US tenants)?

The Core Features spec enforces tenant isolation via RLS on every query. The AI service layer must do the same, but the spec never addresses this.

**Recommendation:** Add a "Multi-Tenancy" section to the Architecture Overview that defines: (a) how tenant context is propagated to the AI service (JWT claim or internal API header), (b) how the PII shield and audit log are scoped per-tenant, (c) how LLM calls are attributed to the correct tenant for billing and compliance.

### 2. LLM Provider Failover Not Defined

The spec mentions "OpenAI / Anthropic (ZDR)" but never defines:
- What happens when the primary provider is unavailable?
- Is there automatic failover to a secondary provider?
- Are there different ZDR agreements per provider?
- How does the system handle provider-specific rate limits?
- What happens when a provider deprecates a model version?

The PRD's risk assessment (Section 13) lists "LLM provider outage" as a risk with "Safe fallback behavior; graceful degradation; output caching where safe" as mitigation. The spec doesn't implement this.

**Recommendation:** Add a "Provider Failover" subsection to the Architecture Overview: primary provider (OpenAI) → secondary (Anthropic) → cached fallback → graceful degradation (feature disabled with clear message). Define the health check mechanism and failover trigger (e.g., 3 consecutive timeouts).

### 3. Token Map Ephemeral Memory Risk

The PII shield stores the token map in memory and destroys it after re-hydration. This means:
- If the service crashes between redaction and re-hydration, the original PII is lost
- If two concurrent requests use the same token namespace, they could collide (e.g., both produce `[NAME_1]`)
- If the LLM response is slow, the token map must be held in memory for the entire duration

The spec says "Never persisted to disk" but doesn't address the crash scenario or concurrency.

**Recommendation:** (a) Use request-scoped namespaces (e.g., `[REQ-abc123-NAME_1]`) to prevent cross-request collisions. (b) Define a timeout for token map retention (e.g., 30 seconds) with automatic cleanup. (c) For the crash scenario, either accept the data loss (and log the trace_id for manual reconstruction) or implement a short-lived in-memory cache with TTL.

### 4. Resume Parsing Confidence Score Formula Is Broken

The confidence score is defined as "percentage of fields populated vs expected." But:
- What fields are "expected"? A resume might legitimately not have certifications, or might not list salary expectations
- A 1-page resume and a 10-page resume have different expected field counts
- The formula treats all fields as equally important (a missing name is the same as a missing certification)

This will produce misleading confidence scores that don't reflect actual parse quality.

**Recommendation:** Use a weighted scoring model: critical fields (name, at least one work entry, at least one skill) weighted 3x, important fields (email, education) weighted 2x, optional fields (certifications, salary) weighted 1x. Define the weights explicitly.

### 5. Passive Recommendations Performance Not Addressed

The spec says passive recommendations are "computed at profile view time (not pre-computed)." For a candidate with 5 skills and an agency with 100 open requisitions, this means:
- 100 LLM comparisons per page load (or batch comparisons)
- Response time will exceed the 2-second acceptance criterion for large datasets
- Cost: ~$0.01 per comparison × 100 = $1.00 per page view

This is economically and technically unsustainable.

**Recommendation:** Define a pre-computation strategy: (a) compute passive recommendations on a schedule (e.g., nightly), (b) incrementally update when candidate profile or requisition changes, (c) cache results in the `job_recommendations` table. The 2-second criterion applies to reading cached results, not computing them.

---

## Gaps by Feature

### 4.2.1 Resume Parsing & Profile Normalization

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Title normalization synonym map not defined | High | Where is the map stored? Database table? Config file? How is it maintained? Who can edit it? Add a `title_synonyms` table or document as configuration. |
| Language detection missing | Medium | What if the resume is in Spanish, German, or Chinese? The NER model is English-only. Either detect language and reject non-English, or add multi-language NER models. |
| Multi-page resume handling | Low | No mention of page limits, OCR for scanned pages, or how very long resumes are chunked for the LLM. |
| Reparse vs original parse path inconsistency | Medium | Original: `POST /api/v1/parse/upload`. Reparse: `POST /api/v1/parse/:candidateId/reparse`. These should follow the same pattern. Use `POST /api/v1/candidates/:id/parse` for both. |
| Concurrent upload race condition | Medium | If the same resume is uploaded twice rapidly, two parsing jobs could run simultaneously. Add idempotency key or dedup on document hash. |
| PII in LLM response | High | The prompt extracts `candidate_name` and `email` from the resume. After PII shield redaction, these fields will be `[NAME_1]` and `[EMAIL_1]`. The LLM will return redacted tokens, not actual values. How does the system map them back? Define the re-hydration step explicitly for parsed fields. |

### 4.2.2 AI-Generated Candidate Profile Summaries

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| `is_edited` flag not in schema | High | The business logic says "stored as `ai_summary` with `is_edited=true`" but the `candidates` table (4.1.2) has no `is_edited` column. Add it. |
| Summary version history | Medium | When a summary is regenerated, is the old version preserved? If a recruiter edits and then regenerates, is the edit lost? Define a `candidate_summary_history` table or document that only the latest is kept. |
| Trigger mechanism undefined | Medium | "Regenerated when: resume re-uploaded, profile fields edited, skills changed" — is this a database trigger, application event, or webhook? Define the event source. |
| Incomplete profile handling | Medium | What if a candidate has skills but no work history? The prompt expects both. Define fallback behavior: use what's available, or require minimum data before generating? |
| Profanity detection service | Low | "Block output, log incident" — what service performs this check? Is it a separate LLM call, a regex filter, or a third-party API? |

### 4.2.3 AI-Driven Job Recommendations

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Passive recommendation cost/performance | High | See Critical Issue #5. Pre-computation is essential. |
| `job_recommendations` missing unique constraint | Medium | Add `UNIQUE (candidate_id, requisition_id, type)` to prevent duplicate entries. |
| Interest notification delivery | Medium | "Notifies the recruiter assigned to the requisition" — via WebSocket? Email? In-app notification? Define the channel. |
| Requisition status change invalidation | Medium | When a requisition is filled/closed, are existing recommendations invalidated? What about candidates who already expressed interest? |
| Tie-breaking for equal fit scores | Low | What if multiple candidates have the same fit_score? Define sort order (e.g., by recency of profile update, or by source priority). |
| "3 data points" threshold | Low | What counts as a data point? Skills? Work entries? Education? Define precisely. |

### 4.2.4 AI Match Support & Ranking

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| `preferred_skills` not in schema | High | The LLM prompt references `preferred_skills` but `requisition_skills` only has `is_required` boolean. Add a `skill_type` column (required/preferred/nice-to-have) or define how preferred skills are identified. |
| Large candidate set handling | Medium | What if 50+ candidates are on a shortlist? The LLM may hit token limits. Define chunking strategy (e.g., batch in groups of 10, merge scores). |
| Skill-count fallback too simplistic | Medium | "Fall back to skill-count ranking" ignores proficiency and experience. Define a weighted fallback: skill match count × proficiency weight × experience years. |
| Post-approval modification | Medium | Can a recruiter add candidates to an approved shortlist? If so, does it require re-approval? Define the workflow. |
| Consistent override tracking | Low | If a recruiter consistently overrides AI rankings, is this flagged? Should there be a threshold (e.g., >80% overrides triggers a review)? |

### 4.2.5 AI Outreach Assistance

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Draft persistence | Medium | "Drafts are not stored server-side" — this means page refresh loses the draft. Is this intentional? If so, document it as a UX constraint. If not, add a drafts table. |
| Hallucinated information in drafts | High | The LLM might invent skills, companies, or achievements not in the candidate's profile. Add a validation step: compare drafted claims against candidate data, flag unsupported assertions. |
| Duplicate outreach prevention | Medium | What if a recruiter generates 5 drafts for the same candidate + job? Is there deduplication? |
| Opted-out candidate handling | Medium | The outreach endpoint must check if the candidate has opted out before generating a draft. Add this validation. |
| Historical response patterns data source | Medium | "Sequence suggestions are based on historical response patterns" — where is this data stored? Define a `outreach_analytics` aggregation table or document that this is deferred to post-v1. |

### 4.2.6 AI Assistant for Recruiters

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Multi-turn conversation context | High | The spec says "query history is stored per-user for the current session only." But follow-up queries ("What are their skills?") require context from the previous query. Define a conversation context store (in-memory with TTL, or session-scoped). |
| Cross-tenant query handling | Medium | The assistant must never return data from other tenants. Ensure the search API (4.1.7) enforces RLS and the assistant doesn't bypass it. |
| Ambiguous intent resolution | Medium | "Show me React" — candidates or jobs? The prompt contract doesn't handle ambiguity resolution. Add a disambiguation step. |
| Aggregated query support | Medium | "How many candidates did I submit this month?" requires aggregation. The search API doesn't support aggregation. Define whether this is in scope or document as a limitation. |
| Suggestion chips personalization | Low | "Based on current pipeline state" — how is this computed? Define the data source and refresh frequency. |

### 4.2.7 PII Privacy Shield Middleware

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Multi-language NER | High | `en_core_web_trf` is English-only. Resumes may be in German, French, Spanish. Define language detection + fallback strategy (reject non-English? use multilingual model?). |
| Image-based PII | Medium | Scanned resumes with photos — NER won't detect faces. Is this in scope? If not, document the limitation. |
| Concurrent request token namespace | Medium | See Critical Issue #3. Use request-scoped token prefixes. |
| Verification UI for large documents | Medium | A 10-page resume with 50+ PII entities — the side-by-side view becomes unwieldy. Define pagination or summary view for large documents. |
| False positive rate measurement | Low | "10% of redacted tokens flagged" — measured over what window? Per-document? Per-day? Per-tenant? Define the measurement scope. |
| Circuit breaker for shield unavailability | Medium | What happens when the shield service is down? Define: (a) fail-open (allow unredacted payloads — compliance risk), (b) fail-closed (block all AI features), or (c) queue and retry. Recommend fail-closed for compliance. |

---

## Cross-Cutting Concerns

| Concern | Severity | Recommendation |
|---------|----------|----------------|
| Data residency for LLM calls | High | EU candidate data must not leave the EU. How does the system ensure LLM API calls for EU tenants are routed to EU-based endpoints? Define region-aware routing. |
| LLM cost management | High | No mention of per-tenant token budgets, cost alerts, or spending caps. An agency processing 500 resumes/day could incur $500+/day in LLM costs. Define budget controls. |
| Model versioning | Medium | When a new GPT-4 version is released, how does the system handle prompt compatibility? Define a model registry and version pinning strategy. |
| A/B testing for prompts | Medium | How do you compare prompt variations? Define a prompt versioning system and experiment framework. |
| LLM response validation | High | Every LLM response should be validated against the expected schema before use. Define a JSON schema validation layer with retry on malformed responses. |
| Token counting and limits | Medium | LLM providers have token limits. Define max input tokens per feature and truncation strategy for large resumes or candidate sets. |

---

## Specific Recommendations (Ranked by Impact)

1. **Define multi-tenancy for the AI service layer** — blocks compliance and billing (Critical Issue #1)
2. **Implement pre-computation for passive recommendations** — blocks performance and cost (Critical Issue #5)
3. **Add LLM provider failover strategy** — blocks availability (Critical Issue #2)
4. **Define token map concurrency safety** — blocks correctness (Critical Issue #3)
5. **Add `preferred_skills` to requisition schema or prompt** — blocks ranking feature (Critical Issue #4)
6. **Add `is_edited` column to candidates table** — blocks summary feature
7. **Define language detection and multi-language handling** — blocks non-English users
8. **Add LLM response JSON schema validation** — prevents silent failures
9. **Define hallucination detection for outreach drafts** — prevents inaccurate outreach
10. **Add per-tenant LLM cost budgets** — prevents runaway costs

---

## Verdict

The spec has strong architectural bones — the PII shield, prompt contracts, and audit logging are well-designed. The critical issues (multi-tenancy, failover, performance, token map safety) must be resolved before implementation. The feature-specific gaps (preferred skills schema, is_edited flag, hallucination detection) are smaller but will cause cascading ambiguity. With these revisions, the spec will be production-ready.
