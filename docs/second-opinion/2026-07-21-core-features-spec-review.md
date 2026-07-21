# Core Features Specification Review

**File Reviewed:** `2026-07-21-core-features-spec.md`

## Overview
The spec outlines the implementation of core features for an AI-Native Agency ATS, covering multi-tenancy, candidate management, job requisition, submission workflow, CRM, client portal, and search/reporting. The data models, API endpoints, and business logic are well-structured and detailed.

## Specific Feedback & Suggestions

### 4.1.1 Multi-Tenant Platform
- **Data Model:** The schema looks robust. Using `gen_random_uuid()` for PKs is standard and good for distributed systems. The `tenant_isolation` RLS policy is well defined.
- **Business Logic:** Hardcoding password hashing (bcrypt cost 12) is fine, but it might be better to delegate this to an external auth provider (Auth0/Okta) sooner rather than later, as managing passwords internally adds security overhead.
- **Suggestion:** Consider adding an `is_deleted` or `deleted_at` field to `organizations` if tenant soft-deletion is a requirement.

### 4.1.2 Candidate Management
- **Data Model:** 
  - `candidate_documents` should probably have a `content_type` (MIME type) column in addition to `document_type`.
  - The `status` enum (`sourced`, `in_review`, etc.) might need to be configurable per tenant in the future, similar to `requisition_stages`.
- **Business Logic:** Relying strictly on exact email match for strong deduplication is good, but phone + name similarity for weak duplicates will need tuning to avoid false positives.

### 4.1.3 Job & Requisition Management
- **Data Model:** 
  - `requisitions` includes `salary_min` and `salary_max`, which is good. You may also want to capture equity or bonus expectations.
  - The `requisition_stages` table allows for per-client configurable stages, which is excellent for agency flexibility.
- **Business Logic:** Linear status transitions (Open → In Progress → Submitted → Filled → Closed) without skipping might be too rigid for real-world scenarios where requisitions are abruptly closed or reopened. Consider allowing flexible state transitions with audit logs.

### 4.1.4 Submission & Workflow Management
- **Data Model:** `shortlist_candidates` tracks `ai_rank` and `recruiter_rank`. Requiring an override reason is a great compliance feature (EU AI Act).
- **Business Logic:** Calculating `fee_amount` automatically based on salary and fee percentage is useful, but there should be a mechanism for flat fees or split commissions if multiple recruiters are involved.

### 4.1.5 Recruiter CRM & Outreach
- **Data Model:** `outreach_sequences` stores steps in a JSONB array. This is flexible, but it might be harder to query if you need to find all sequences using a specific template.
- **Business Logic:** Manual trigger for sequence automation in v1 is a safe and practical approach.

### 4.1.6 Client Portal (Read-Only)
- **Data Model:** `client_portal_sessions` is well thought out with OTP limits and magic link expirations.
- **Business Logic:** Locking the session to a single requisition is secure. Pushing feedback back via WebSockets is a nice touch for real-time collaboration.

### 4.1.7 Search & Reporting
- **Data Model:** Storing search queries in `search_log` is a great idea for building future features like "recent searches" or "saved searches."
- **Business Logic:** Using PostgreSQL full-text search with GIN indexes is a solid architectural choice for a v1. Relying on materialized views for dashboards is good for performance, but 15-minute staleness might frustrate users if they expect real-time updates after moving a candidate in the Kanban view.

## Conclusion
The specification is comprehensive and provides a clear path to implementation. The schema designs and API endpoints are logically aligned with the user stories. Addressing the minor suggestions above (e.g., MIME types, flexible state transitions) will further strengthen the v1 GA release.
