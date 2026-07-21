# Core Features Implementation Plan — Review

**Reviewer:** MIMO (automated plan review)
**Date:** 2026-07-21
**Source:** `docs/superpowers/plans/2026-07-21-core-features-impl.md`
**Spec:** `docs/superpowers/specs/2026-07-21-core-features-spec.md`

---

## Summary

The plan covers all 7 spec sections (4.1.1–4.1.7) across 8 phases and 21 tasks with detailed step-by-step implementations. Structure is sound: Phase 0 builds foundations, subsequent phases depend correctly on prior ones, and file paths are concrete. Overall quality is high — the plan is directly executable.

---

## Findings

### 1. Strengths

- **Phase ordering is correct.** Phase 0 (foundation) → Phase 1 (platform) → Phase 2 (candidates) → Phase 3 (requisitions) → Phase 4 (shortlists) → Phase 5 (CRM) → Phase 6 (portal) → Phase 7 (search). Each phase depends on the prior.
- **File paths are concrete.** Every task specifies exact `Create:` and `Modify:` file paths with module-level granularity.
- **Interfaces are bidirectional.** Each task declares both `Consumes` and `Produces`, making dependency wiring clear.
- **Test requirements are explicit.** Every task ends with a test step specifying what to verify.
- **Global constraints are well-defined.** Pagination, rate limits, error envelope, soft-delete, RLS — all documented at the top and consistently referenced.

### 2. Issues Found

#### 2.1 Missing: Candidate List Endpoint in Task 2.3

**Spec:** 4.1.2 defines `GET /api/v1/candidates` (list/search candidates, paginated, filtered).
**Plan Task 2.3:** Implements GET/:id, PUT/:id, DELETE/:id, upload, status, dedup, documents, timeline — but no list endpoint.
**Impact:** Candidates cannot be listed or searched.
**Fix:** Add `GET /api/v1/candidates` with pagination, filters (status, source, owner, skill), and search to Task 2.3 Step 7.

#### 2.2 Missing: `token_version` Column on Users Model

**Spec:** 4.1.1 JWT section: "Revocation: on password change, role change, user deactivation — all active sessions for that user are invalidated by incrementing a `token_version` counter on the user record."
**Plan Task 0.3:** Step 3 mentions `verify_token()` with "token_version check" but the User model in Task 1.1 Step 2 doesn't include a `token_version` column.
**Impact:** Token revocation mechanism has no storage backing.
**Fix:** Add `token_version INT NOT NULL DEFAULT 0` to the User model definition in Task 1.1 Step 2.

#### 2.3 Missing: `owner_id` Column on Candidates

**Spec:** 4.1.2 candidates table: `owner_id UUID FK -> users.id, nullable`.
**Plan Task 2.1 Step 1:** Says "all columns from spec" but doesn't explicitly list `owner_id`. The deactivation behavior (set candidates' `owner_id = null`) is mentioned in Task 1.3 Step 2 but the column isn't called out in the model definition.
**Impact:** Ambiguous — an implementer might miss `owner_id` on the Candidate model.
**Fix:** Explicitly list `owner_id` in Task 2.1 Step 1 column checklist.

#### 2.4 Missing: `source` Column Enum on Candidates

**Spec:** 4.1.2: `source VARCHAR(100) NOT NULL (linkedin, dribbble, github, referral, agency_db, manual)`.
**Plan Task 2.1 Step 1:** Says "all columns from spec" but doesn't call out the source enum values.
**Impact:** Implementer may not know which source values are valid.
**Fix:** Add the source enum values to Task 2.1 Step 1.

#### 2.5 Missing: Requisition `client_name` Derivation

**Spec:** 4.1.3: "`client_name` is derived from `client_contacts.client_name` — not stored as a separate string."
**Plan Task 3.2 Step 1:** Lists GET/:id "with skills, client contact, pipeline counts" but doesn't specify the client_name derivation.
**Impact:** Minor — the plan doesn't store client_name on requisition (correct), but the GET response should include it via JOIN.
**Fix:** Clarify in Task 3.2 Step 1 that GET/:id response includes `client_name` via JOIN on client_contacts.

#### 2.6 Missing: `POST /api/v1/client-portal/generate-link` Endpoint

**Spec:** 4.1.6 defines `POST /api/v1/client-portal/generate-link` — "Generate magic link for client."
**Plan Task 6.2:** Implements verify, verify-otp, submissions, feedback, revoke, access-log — but no generate-link endpoint. The link generation is described in Task 6.1 Step 4 as a function, but the API endpoint to trigger it from the recruiter side is missing.
**Impact:** Recruiters have no way to generate portal links for clients.
**Fix:** Add `POST /api/v1/client-portal/generate-link` to Task 6.2 as Step 1, consuming the magic link generation from Task 6.1.

#### 2.7 Missing: `last_accessed_at` on Client Portal Sessions

**Spec:** 4.1.6: `client_portal_sessions` has `last_accessed_at TIMESTAMPTZ nullable`.
**Plan Task 6.1 Step 1:** Lists columns but omits `last_accessed_at`.
**Impact:** Portal access tracking won't record last activity.
**Fix:** Add `last_accessed_at` to the ClientPortalSession model in Task 6.1 Step 1.

#### 2.8 Missing: WebSocket Reconnection Strategy

**Spec:** 4.1.6: "WebSocket reconnection uses exponential backoff (1s, 2s, 4s)."
**Plan Task 6.2 Step 7:** Says "exponential backoff reconnection" but doesn't specify the cadence.
**Impact:** Minor — implementer may choose different backoff intervals.
**Fix:** Specify the backoff values (1s, 2s, 4s) in Task 6.2 Step 7.

#### 2.9 Missing: `POST /api/v1/outreach-templates` Path vs `POST /api/v1/templates`

**Spec:** 4.1.5 uses path `/api/v1/outreach-templates`.
**Plan Task 5.2 Step 2:** Says "template CRUD" without specifying the exact path prefix.
**Impact:** Ambiguous — implementer might use `/api/v1/templates` instead of `/api/v1/outreach-templates`.
**Fix:** Specify the exact path prefix `/api/v1/outreach-templates` in Task 5.2 Step 2.

#### 2.10 Missing: `POST /api/v1/outreach-sequences` Path vs `POST /api/v1/sequences`

**Spec:** 4.1.5 uses path `/api/v1/outreach-sequences`.
**Plan Task 5.2 Step 3:** Says "sequence CRUD" without specifying the exact path prefix.
**Impact:** Same as above.
**Fix:** Specify the exact path prefix `/api/v1/outreach-sequences` in Task 5.2 Step 3.

#### 2.11 Missing: `performed_at` on Activities Model

**Spec:** 4.1.5: `activities` has `performed_at TIMESTAMPTZ NOT NULL, DEFAULT now()`.
**Plan Task 5.1 Step 6:** Lists `performed_by` but omits `performed_at`.
**Impact:** Activities won't have a timestamp field (though `created_at` may serve the same purpose — but the spec defines both).
**Fix:** Add `performed_at` to the Activity model in Task 5.1 Step 6.

#### 2.12 Missing: Sourcing List `created_at`

**Spec:** 4.1.5: `sourcing_lists` has `created_at TIMESTAMPTZ DEFAULT now()`.
**Plan Task 5.1 Step 1:** Lists columns but omits `created_at`.
**Impact:** Minor — the global constraint says all entities have `created_at`, so this is implied.
**Fix:** No action needed — covered by global constraints.

#### 2.13 Missing: Search Ranking Boosts

**Spec:** 4.1.7: Search ranking uses `ts_rank * recency_boost * owner_boost` with specific values (+0.2 for recency, +0.1 for owner).
**Plan Task 7.1 Step 4:** Mentions "ranking (ts_rank * recency_boost * owner_boost)" but doesn't specify the boost values.
**Impact:** Implementer may choose different boost multipliers.
**Fix:** Specify the boost values (+0.2 recency, +0.1 owner) in Task 7.1 Step 4.

#### 2.14 Missing: POST Search Endpoint Fallback

**Spec:** 4.1.7: "if the combined query string exceeds 4,000 characters, clients should use `POST /api/v1/search/candidates` with a JSON body instead."
**Plan Task 7.1 Step 4:** Only implements GET endpoint with 414 response — doesn't implement the POST fallback.
**Impact:** Clients with complex filters have no alternative when URL exceeds 4K chars.
**Fix:** Add `POST /api/v1/search/candidates` and `POST /api/v1/search/requisitions` as fallback endpoints in Task 7.1.

#### 2.15 Missing: `requisition_stages` Path Prefix

**Spec:** 4.1.5 defines paths as `/api/v1/requisition-stages` (plural).
**Plan Task 3.2 Step 4:** Says "GET, POST, PUT/:id, DELETE/:id (blocked if in use), POST/:id/reorder-stages" but doesn't specify whether stages are nested under requisitions or at the top level.
**Impact:** The spec defines them as top-level (`/api/v1/requisition-stages`) with a separate reorder endpoint on the requisition (`/api/v1/requisitions/:id/reorder-stages`). The plan conflates them.
**Fix:** Clarify in Task 3.2 Step 4 that stage CRUD is at `/api/v1/requisition-stages` (top-level) and reorder is at `/api/v1/requisitions/:id/reorder-stages`.

#### 2.16 Missing: `created_at`/`updated_at` on Several Models

**Spec:** Global constraints: "All entities must have `created_at` and `updated_at` timestamptz columns with `now()` default."
**Plan:** Several models (SourcingList, OutreachTemplate, OutreachSequence, etc.) list `created_at` but not `updated_at`.
**Impact:** Inconsistent with global constraints.
**Fix:** Add `updated_at` to all models that currently only have `created_at`.

---

## Verdict

**Conditionally Approve** — 16 findings, 2 high-severity (missing candidate list endpoint, missing generate-link portal endpoint), 4 medium-severity (token_version column, POST search fallback, path prefix clarity, last_accessed_at), 10 low-severity (enum values, column details, boost values, backoff values). The plan is structurally sound and the high-severity items are straightforward to fix.

---

## Recommendations

1. **Fix the 2 high-severity gaps immediately** before implementation begins.
2. **Add a "Column Checklist" subsection to each model task** listing every column from the spec — prevents omissions.
3. **Specify exact API path prefixes in every endpoint task** — avoids ambiguity between `/api/v1/templates` vs `/api/v1/outreach-templates`.
4. **Add a "WebSocket Events" subsection to Phase 6** listing all events, channels, and payloads.
