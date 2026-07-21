# Second Opinion Review: Core Features Implementation Specification

**Reviewer:** MIMO v2.5  
**Date:** 2026-07-21  
**Spec Under Review:** `docs/superpowers/specs/2026-07-21-core-features-spec.md`  
**Verdict:** REVISIONS NEEDED — Solid foundation with structural gaps that will cause ambiguity during implementation  

---

## Summary

The spec is well-structured and covers the right surface area. Each feature follows a consistent template (User Story → Data Model → API → UI → Business Logic → Integration → Acceptance Criteria). The schema designs are sensible, the API contracts are clear, and the acceptance criteria are testable. However, there are material gaps in data modeling, missing entity definitions, incomplete lifecycle coverage, and several cross-cutting concerns that are never addressed. These will surface as blockers during implementation.

---

## Strengths

1. **Consistent structure.** Every feature section follows the same template, making it easy to scan and compare depth across sections.

2. **Pragmatic schema design.** Tables use appropriate types, sensible defaults, and correct FK relationships. The `shortlist_candidates` rank/override pattern is a clean implementation of the EU AI Act human oversight requirement.

3. **Clear API contracts.** Endpoint tables list method, path, and description. The search query parameter example in 4.1.7 is particularly useful.

4. **Integration points are explicit.** Every feature lists its dependencies on other features, which will help when planning implementation order and identifying circular dependencies.

5. **Acceptance criteria are testable.** Most criteria are concrete and verifiable (e.g., "OTP verification succeeds within 10 minutes").

---

## Critical Issues

### 1. Missing Entity Definitions

**`client_contacts` table is referenced but never defined.**

`requisitions.client_contact_id` references a `client_contacts` table that does not exist in the spec. The `activities.client_contact_id` column also references it. Without this table, the CRM, requisition, and activity features cannot be properly linked.

**Recommendation:** Add a `client_contacts` table with at minimum: `id`, `organization_id`, `client_name`, `contact_name`, `email`, `phone`, `role`, `created_at`. This is a foundational entity that the CRM, client portal, and requisition features all depend on.

### 2. SuperAdmin Role Not Defined

The API endpoint `POST /api/v1/organizations` requires `SuperAdmin` auth, but the `users.role` CHECK constraint only allows `('admin','recruiter','client_readonly')`. SuperAdmin is not a tenant-level role — it's a platform-level role. This means:
- SuperAdmin users are not in the `users` table (or they're in a separate table)
- The API endpoint is actually a platform provisioning endpoint, not a tenant endpoint
- This distinction is never clarified

**Recommendation:** Either (a) add a `platform_users` table with SuperAdmin role, separate from tenant users, or (b) clarify that SuperAdmin is an internal/system role not visible to tenant admins, and document how platform admins are managed.

### 3. Candidate Status Transitions Undocumented

The `candidates.status` CHECK constraint lists 7 possible states but there is no definition of which transitions are valid. For example:
- Can a candidate go from `sourced` directly to `interviewing`?
- Can a `placed` candidate be moved back to `submitted`?
- Can a `rejected` candidate be reactivated to `in_review`?
- Who is authorized to make each transition?

Without transition rules, the UI and API will need to be designed with arbitrary restrictions that don't match business reality.

**Recommendation:** Add a state machine diagram or transition table:
```
sourced → in_review → submitted → interviewing → placed
   ↓          ↓           ↓            ↓
rejected   rejected    rejected     rejected → archived
                       withdrawn
```
Document who can trigger each transition and whether a reason is required.

### 4. `outreach_sequences.steps` as JSONB Breaks Referential Integrity

The `steps` column stores an ordered array of objects with `template_id`. This means:
- No FK constraint on `template_id` — deleting a template breaks the sequence silently
- No way to query "which sequences use template X?" without JSONB traversal
- No way to enforce valid step structure at the database level

**Recommendation:** Replace with a `sequence_steps` junction table:
```sql
sequence_steps (
  id UUID PK,
  sequence_id UUID FK -> outreach_sequences,
  template_id UUID FK -> outreach_templates,
  step_order INT NOT NULL,
  delay_hours INT NOT NULL,
  channel VARCHAR(20) NOT NULL
)
```

### 5. Placement Fee Computation Undefined

`placements.fee_amount` is listed as "computed" but there's no definition of:
- Is it a computed column (PostgreSQL GENERATED ALWAYS AS)?
- Is it computed by application logic on write?
- Is it computed on read?
- Is it recalculated if `fee_percentage` or `salary` changes after placement?

**Recommendation:** Explicitly define as a generated column or document the application-layer computation with the exact formula and update behavior. Example: `fee_amount = salary * fee_percentage / 100`, recomputed on any change to salary or fee_percentage.

---

## Gaps by Feature

### 4.1.1 Multi-Tenant Platform

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| No user invitation flow defined | High | Add invitation workflow: admin sends invite → email with magic link → user sets password → account activated. Or clarify that admin creates accounts directly. |
| No password reset flow | High | Add forgot-password flow: email with reset link → new password → session invalidation. |
| No session/token management details | Medium | Document JWT structure (org_id, user_id, role in claims), refresh token rotation, revocation strategy. |
| No tenant provisioning/activation workflow | Medium | How does a new agency sign up? Is there a self-serve flow or is it admin-only? |
| `users` table missing UNIQUE on (organization_id, email) | Medium | Add partial unique index: `CREATE UNIQUE INDEX idx_users_org_email ON users(organization_id, email) WHERE is_active = true;` |
| `organizations.slug` has no uniqueness scope | Low | Confirm slug is globally unique, not just per-tenant. |
| No mention of RLS middleware implementation | Medium | Document how `app.organization_id` is set (e.g., from JWT claim in connection pool or per-request SET LOCAL). |

### 4.1.2 Candidate Management

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| No candidate ownership/assignment workflow | High | Who sets `owner_id`? Can ownership be transferred? What happens when a recruiter leaves? Document assignment rules. |
| No candidate status transition rules | High | See Critical Issue #3 above. |
| `candidate_skills` missing unique constraint | Medium | Add `UNIQUE (candidate_id, skill_name)` to prevent duplicate skill entries. |
| Dedup name matching algorithm undefined | Medium | "Phone + name similarity = weak duplicate" — what similarity algorithm? Jaro-Winkler? Levenshtein? What threshold? |
| No batch upload support mentioned | Low | The PRD mentions "scale candidate intake" — is bulk CSV upload in scope? If not, explicitly exclude it. |
| No mention of candidate notes/annotations | Low | Recruiters typically need a scratchpad per candidate. Is this in the `candidate_timeline` metadata or a separate feature? |
| Acceptance criteria too vague | Medium | "Searching candidates by name, skill, or source returns correct results" — define what "correct" means. Add: "returns candidates matching the search term within 200ms." |

### 4.1.3 Job & Requisition Management

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| `requisition_stages` table has no API | High | The table is defined but no endpoints exist to create, update, or delete stages. Add CRUD endpoints. |
| `client_name` is a plain string, not an entity | Medium | If `client_contacts` exists, `client_name` should either be a FK to a `clients` table or derived from the contact. A plain string will lead to inconsistency ("TechCorp" vs "Tech Corp" vs "techcorp"). |
| Requisition status transition rules incomplete | Medium | "Linear, no skipping" is stated but the path from `submitted` to `filled` skips `in_progress`. Clarify: can `submitted` go to `in_progress` (e.g., if more candidates needed)? |
| No requisition cloning/template feature | Low | Agencies often fill similar roles repeatedly. Mention whether cloning is in scope or explicitly out of scope. |
| No requisition visibility rules within an org | Medium | Can all recruiters see all requisitions? Or only those they own? Document access control within the tenant. |

### 4.1.4 Submission & Workflow Management

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| `ai_rank` population mechanism unclear | High | The column exists but there's no mention of when it's set. Is it populated by the AI match service (4.2.4) on shortlist creation? On demand? Document the trigger. |
| No recycle pool table | Medium | "Moved to recycle pool" is mentioned but there's no table or status to represent this. Add a `recycled_candidates` table or define how the recycle state is represented. |
| Multiple shortlists per requisition | Medium | Can a recruiter create shortlist A (senior candidates) and shortlist B (junior candidates) for the same job? The data model allows it but the workflow implications aren't discussed. |
| Shortlist limits undefined | Low | Max candidates per shortlist? Is there a business rule? |
| Interview `stage` is a free-text string | Medium | Should this reference `requisition_stages`? Otherwise, interview stages are inconsistent across shortlists for the same job. |
| No interview scheduling details | Medium | Does the system manage calendar slots? Is there a booking flow? Or is interview scheduling done externally and just logged? |

### 4.1.5 Recruiter CRM & Outreach

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| No email deliverability tracking | Medium | Bounces, opens, clicks, spam complaints — are these tracked in v1 or deferred? |
| No opt-out/unsubscribe management | High | Legal requirement under CAN-SPAM, GDPR. If outreach is email-based, unsubscribe must be handled. At minimum, document that recipients can reply STOP. |
| No outreach rate limiting | Medium | Per-candidate, per-day limits to prevent spam. What are the limits? |
| Activity vs candidate_timeline confusion | Medium | Both tables track events. The acceptance criteria says "Sending an outreach creates a timestamped activity on the candidate's timeline" — which table gets the event? Both? Clarify the relationship. |
| `client_contact_id` has no FK target | High | Same as Critical Issue #1 — references undefined `client_contacts` table. |

### 4.1.6 Client Portal

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| No portal branding/whitelabeling | Low | The PRD says "single-branded UI at launch (no tenant-level white-labeling in v1)" — confirm this applies to the client portal too, or document whether agencies can customize the portal look. |
| No portal access logging | Medium | Which client viewed which candidate, when, for how long? This is valuable data for the recruiter. Add a `portal_access_log` table. |
| No multi-requisition portal | Low | Can a client have one portal link that shows candidates across multiple jobs? Or is it strictly one link per requisition? |
| WebSocket feedback mechanism undefined | Medium | "Feedback is pushed back to the recruiter's pipeline view in real-time via WebSocket event" — document the WebSocket subscription model, reconnection strategy, and fallback if WebSocket is unavailable. |
| No client portal session invalidation | Medium | What happens when the recruiter revokes access (e.g., client relationship ends)? Add an endpoint to invalidate all sessions for a client. |

### 4.1.7 Search & Reporting

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Search ranking algorithm undefined | Medium | "Ordered by match relevance" — how is relevance computed? TF-IDF? BM25? Recency? Document the ranking function. |
| Materialized view refresh strategy too slow for pipeline | Medium | 15-minute refresh means pipeline counts can be stale for up to 15 minutes. Consider: event-driven refresh on status change, or at minimum document that staleness is acceptable for v1. |
| No saved searches | Low | Is this in scope? If not, explicitly exclude it. |
| No search analytics | Low | What are recruiters searching for? Zero-result queries? Useful for product improvement. Mention whether this is tracked. |
| Export handling for large datasets | Medium | What happens with 10,000+ candidates? Pagination? Streaming? Memory limits? |
| No dashboard customization | Low | Can users reorder/configure widgets? Or is the dashboard static? |

---

## Cross-Cutting Concerns (Not Addressed in Any Feature)

| Concern | Severity | Recommendation |
|---------|----------|----------------|
| Error response format | High | Define a standard error response schema: `{ error: { code: string, message: string, details?: object } }`. Which HTTP status codes for which error types? |
| Pagination strategy | High | Offset-based or cursor-based? Define page/limit parameters, max limit, default limit. The search endpoint mentions pagination but the candidate list endpoint doesn't. |
| API versioning strategy | Medium | The spec uses `/api/v1/` but never defines versioning policy. How will breaking changes be handled? |
| Rate limiting strategy | Medium | Per-tenant? Per-user? Per-endpoint? What are the limits? What's the response on 429? |
| Request correlation IDs | Medium | Every request should propagate a `X-Request-ID` for distributed tracing. Is this handled by the API gateway? |
| Multi-region data residency | Medium | The PRD specifies US/UK/EU regions. The spec mentions `data_region` on organizations but never explains how the API routes to the correct region or how cross-region queries work. |
| Testing strategy | Medium | No mention of unit test coverage targets, integration test approach, or E2E test strategy. |
| Accessibility | Medium | WCAG 2.1 AA compliance? Screen reader support? Keyboard navigation? This should be a cross-cutting requirement. |
| Loading/empty/error UI states | Low | The UI Components sections list populated states but rarely mention skeleton loaders, empty states, or error states. Add for each component. |

---

## Specific Recommendations (Ranked by Impact)

1. **Add `client_contacts` table** — blocks CRM, requisitions, and activities (Critical Issue #1)
2. **Define candidate status state machine** — blocks UI and API validation (Critical Issue #3)
3. **Replace `outreach_sequences.steps` JSONB with junction table** — prevents data integrity issues (Critical Issue #4)
4. **Document SuperAdmin role separation** — blocks tenant provisioning (Critical Issue #2)
5. **Define placement fee computation explicitly** — prevents business logic ambiguity (Critical Issue #5)
6. **Add `requisition_stages` CRUD endpoints** — table exists but has no API
7. **Add standard error response schema** — prevents inconsistent error handling across features
8. **Define pagination strategy** — prevents inconsistent list endpoints
9. **Clarify activity vs candidate_timeline relationship** — prevents duplicate event storage
10. **Add portal access logging** — valuable for recruiter analytics, low implementation cost

---

## Verdict

The spec is a strong starting point with clear structure and sensible designs. The critical issues (missing entity definitions, undefined state machines, JSONB referential integrity) must be resolved before implementation begins — they will cause cascading ambiguity. The cross-cutting concerns (error handling, pagination, rate limiting) should be extracted into a shared conventions section to avoid each feature reinventing them. With these revisions, the spec will be implementation-ready.
