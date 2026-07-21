# AI-Native Features Implementation Plan — Review

**Reviewer:** MIMO (automated plan review)
**Date:** 2026-07-21
**Source:** `docs/superpowers/plans/2026-07-21-ai-native-features-impl.md`
**Spec:** `docs/superpowers/specs/2026-07-21-ai-native-features-spec.md`

---

## Summary

The plan covers all 7 spec sections (4.2.1–4.2.7) across 8 phases and 19 tasks. The architecture correctly places the PII Shield as the mandatory gateway, implements provider failover with rollback, and tracks costs per AI operation. Phase ordering is correct: foundation → shield → parsing → summaries → recommendations → ranking → outreach → assistant. The plan is directly executable.

---

## Findings

### 1. Strengths

- **PII Shield is correctly prioritized as Phase 1.** All subsequent AI features depend on it, and the plan enforces this dependency.
- **LLM Router implementation is thorough.** Per-region routing, rollback cadence, cost calculation, and rate limit awareness are all addressed in Task 0.3.
- **Confidence scale is standardized.** High >= 0.85, Medium 0.50–0.84, Low < 0.50 — consistent across all features.
- **Hallucination detection is cross-feature.** Task 2.2 implements it, and Task 6.8 correctly wires it into outreach drafting.
- **Token budget management is defined.** 500K default, 120% hard cap, 80%/100% alerts — all in Global Constraints.
- **Request-scoped token namespaces.** `[REQ-{trace_id}-TYPE_N]` prevents cross-request collisions — correctly specified.

### 2. Issues Found

#### 2.1 Missing: `GET /api/v1/candidates/:id/summary` Implementation Detail

**Spec:** 4.2.2 defines `GET /api/v1/candidates/:id/summary` — "Get current AI summary."
**Plan Task 3.1 Interfaces:** Lists this endpoint in the `Produces` line, but no step implements it.
**Impact:** The summary read endpoint is declared but never built. The candidate portal and client portal both need to read summaries.
**Fix:** Add a step in Task 3.1: "Implement `GET /api/v1/candidates/:id/summary` — return `ai_summary`, `ai_summary_generated_at`, `is_ai_summary_edited` from the candidates table."

#### 2.2 Missing: `GET /api/v1/requisitions/:id/recommended-candidates` Response Format

**Spec:** 4.2.3 defines this endpoint — "Get candidates ranked for this job (recruiter)."
**Plan Task 4.2 Step 2:** Implements the endpoint but doesn't specify the response shape.
**Impact:** Implementer doesn't know what fields to return (fit_score? skill_match? gap_analysis?).
**Fix:** Specify the response: array of `{ candidate_id, fit_score, skill_match: { matched, missing }, gap_analysis, recommendation }` sorted by fit_score descending.

#### 2.3 Missing: `GET /api/v1/shortlists/:id/rankings` Response Format

**Spec:** 4.2.4 defines `GET /api/v1/shortlists/:id/rankings` — "Get current AI rankings for shortlist."
**Plan Task 5.1 Step 5:** Implements the endpoint but doesn't specify the response shape.
**Impact:** Implementer doesn't know whether to return shortlist_candidate records, fit scores, or both.
**Fix:** Specify the response: array of `{ shortlist_candidate_id, candidate_id, ai_rank, fit_score, skill_match, strengths, concerns, recommendation }` ordered by ai_rank.

#### 2.4 Missing: Re-parse Trigger via API

**Spec:** 4.2.3 defines `POST /api/v1/candidates/:id/parse` with the note: "Re-run parse (e.g., after document update)."
**Plan Task 2.3 Step 1:** Only implements initial parse — no re-parse endpoint.
**Impact:** Recruiters cannot trigger a re-parse after editing candidate fields.
**Fix:** Add `POST /api/v1/candidates/:id/parse` as a re-parse endpoint in Task 2.3 (same path, different behavior: re-parses existing document).

#### 2.5 Missing: Max Token Limit Per Feature

**Spec:** Cross-cutting concerns: "Max input tokens per feature defined in each section. Text exceeding the limit is truncated from the bottom (oldest content first)."
**Plan Global Constraints:** Mentions "Token budget per tenant: 500K input tokens/day default" but doesn't define per-feature token limits.
**Impact:** No guidance on how much text to send to the LLM for each feature. Resume parsing could send 50K tokens while summaries send 2K.
**Fix:** Add per-feature max token limits to the plan or reference the spec sections that define them.

#### 2.6 Missing: Model Version Pinning in LLM Router

**Spec:** Architecture: "Model version pinning: Each provider + model combination is pinned in a model registry (e.g., `openai/gpt-4o-2026-05-13`, `anthropic/claude-3.5-sonnet-2026-06-01`). Version upgrades are explicit config changes, not automatic."
**Plan Task 0.3:** Implements the router but doesn't mention model version pinning or the registry lookup.
**Impact:** The router might use the latest model version instead of a pinned one, causing reproducibility issues.
**Fix:** Add a step in Task 0.3: "Before each LLM call, look up the pinned model version from `ai_model_versions` registry; use only the pinned version."

#### 2.7 Missing: `ai_model_versions` Seed Data

**Spec:** Architecture: "Model registry table: `ai_model_versions(model_name, version, active_from, prompt_version)`."
**Plan Task 0.4 Step 4:** Says "Seed the registry with the prompt contracts from spec sections 4.2.1–4.2.6" but doesn't specify the initial model versions.
**Impact:** Implementer doesn't know which model versions to pin initially.
**Fix:** Specify initial seed data: `openai/gpt-4o-2026-05-13`, `anthropic/claude-3.5-sonnet-2026-06-01` (or whatever is current at implementation time).

#### 2.8 Missing: Passive Recommendation Incomplete Profile Guard

**Spec:** 4.2.3: "If candidate profile has < 3 data points (skills ≥ 1, work history ≥ 1, education ≥ 1), passive recommendations show 'Complete your profile to get personalized recommendations'."
**Plan Task 4.1 Step 3:** The recompute worker compares "all complete profiles" but doesn't define what "complete" means.
**Impact:** Ambiguous — implementer may include profiles with only 1 skill and no work history.
**Fix:** Define "complete profile" in Task 4.1 Step 3: skills ≥ 1, work_history ≥ 1, education ≥ 1.

#### 2.9 Missing: Recommendation Invalidation on Requisition Close/Fill

**Spec:** 4.2.3: "when a requisition is filled or closed, existing recommendations for that requisition are invalidated (candidates who already expressed interest receive a notification that the role is no longer available)."
**Plan Task 4.1 Step 5:** Handles "requisition open/close/skill change" but doesn't mention invalidation or interest notifications.
**Impact:** Candidates who expressed interest in a filled/closed role won't be notified.
**Fix:** Add to Task 4.1 Step 5: "On requisition close/fill, mark all recommendations for that requisition as inactive; send notification to candidates who expressed interest."

#### 2.10 Missing: Tie-Breaking for Equal Fit Scores

**Spec:** 4.2.3: "Tie-breaking for equal fit scores: sort by `computed_at` descending (most recently computed first)."
**Plan Task 4.1:** No mention of tie-breaking.
**Impact:** Minor — implementer may sort arbitrarily.
**Fix:** Add tie-breaking rule to Task 4.1 or Task 4.2.

#### 2.11 Missing: Outreach Draft Storage Policy

**Spec:** 4.2.5: "Drafts are not stored server-side — they are generated on-demand and discarded after the session."
**Plan Task 6.1:** Implements draft generation but doesn't mention the no-storage policy.
**Impact:** Implementer might store drafts in a database table, which contradicts the spec.
**Fix:** Add an explicit note in Task 6.1: "Drafts are ephemeral — returned in the response body only, not persisted to database."

#### 2.12 Missing: Assistant Session Max Duration

**Spec:** 4.2.6: "TTL: 30 minutes of inactivity, max 1 hour total."
**Plan Task 7.1 Step 2:** Says "TTL 30min" but doesn't mention the 1-hour max duration.
**Impact:** Sessions could persist beyond 1 hour.
**Fix:** Add the 1-hour max duration to Task 7.1 Step 2.

#### 2.13 Missing: Assistant Aggregate Queries

**Spec:** 4.2.6: "Aggregate queries (e.g., 'How many candidates did I submit this month?') are supported via the search API's `_meta` endpoint that returns count-only for a query."
**Plan Task 7.1:** No mention of aggregate/count queries.
**Impact:** The assistant won't support "how many" type questions.
**Fix:** Add a step in Task 7.1: "Implement aggregate query support — when LLM detects a count/aggregation intent, call the search API's `_meta` endpoint for count-only results."

#### 2.14 Missing: Shield `trace_id` in Internal Headers

**Spec:** 4.2.7: "All internal endpoints accept `X-Organization-ID` and `X-Trace-ID` headers for tenant attribution and tracing."
**Plan Task 1.2:** Lists `X-Organization-ID` and `X-User-ID` but not `X-Trace-ID`.
**Impact:** Trace correlation between shield calls and AI features won't work.
**Fix:** Add `X-Trace-ID` to the internal header list in Task 1.2.

#### 2.15 Missing: Shield Token Map 100-Entry Limit

**Spec:** 4.2.7 error states: "Token map exceeds 100 entries for single payload → Return error 'Payload too complex — split into smaller segments'."
**Plan Task 1.1:** No mention of the 100-entry limit on the TokenMap.
**Impact:** Large resumes with 200+ PII entities could cause memory issues.
**Fix:** Add the 100-entry limit to the TokenMap implementation in Task 1.1 Step 4.

#### 2.16 Missing: NER Entity List Completeness

**Spec:** 4.2.7 NER config: "Entities tracked: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, STREET_ADDRESS, DATE_OF_BIRTH, CREDIT_CARD, SSN, PASSPORT, DRIVERS_LICENSE, BANK_ACCOUNT."
**Plan Task 1.1 Step 1:** Lists "PERSON, EMAIL_ADDRESS, PHONE_NUMBER, etc." — the "etc." is vague.
**Impact:** Implementer may miss critical entity types like CREDIT_CARD, BANK_ACCOUNT, SSN.
**Fix:** List all 10 entity types explicitly in Task 1.1 Step 1.

---

## Verdict

**Conditionally Approve** — 16 findings, 3 high-severity (missing summary GET implementation, missing re-parse endpoint, missing model version pinning), 5 medium-severity (response formats, token limits, recommendation invalidation, draft storage policy, trace_id header), 8 low-severity (tie-breaking, session max duration, aggregate queries, entity list, token map limit, seed data, profile completeness definition, recommended-candidates response). The plan is structurally sound and the high-severity items are straightforward to fix.

---

## Recommendations

1. **Fix the 3 high-severity gaps immediately** before implementation begins.
2. **Add a "Response Shape" subsection to every GET endpoint task** — specify exact JSON fields returned.
3. **Add a "Token Limits" subsection to the Global Constraints** — define per-feature max input tokens.
4. **Add an "Implementation Notes" block to Task 0.3 (LLM Router)** listing model version pinning, registry lookup, and version upgrade policy.
5. **Consider adding a "Spec Cross-Reference" column to each task** mapping back to the exact spec section — prevents omissions during implementation.
