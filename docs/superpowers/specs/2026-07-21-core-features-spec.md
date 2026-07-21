# Core Features — Implementation Specification

**Product:** AI-Native Agency ATS  
**PRD Reference:** Section 4.1 (Core Features)  
**Target Version:** v1.0 GA  
**Status:** Revised Draft (incorporating second-opinion review 2026-07-21)

---

## Cross-Cutting Conventions

These conventions apply to every feature section below.

### Error Response Format

All API endpoints return a consistent error envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      { "field": "email", "reason": "must be a valid email address", "code": "invalid_format" }
    ]
  }
}
```

| HTTP Status | Usage |
|-------------|-------|
| 400 | Validation error — malformed request body or parameters |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict — duplicate resource, invalid state transition |
| 422 | Business rule violation — e.g., override reason required |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

### Pagination Strategy

All list endpoints use **cursor-based pagination** (offset-based is not supported):

| Query Parameter | Type | Default | Description |
|-----------------|------|---------|-------------|
| cursor | string | null | Opaque cursor from previous response; omit for first page |
| limit | int | 25 | Max 100 |
| sort | string | "created_at:desc" | `field:direction` |

Response envelope:

```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "eyJpZCI6IjEyMyJ9",
    "has_more": true,
    "total": 342
  }
}
```

### Rate Limiting

- Per-tenant: 1000 req/min (all endpoints)
- Per-user: 200 req/min
- Burst: 50 req/s burst allowance
- Response on limit: `429 Too Many Requests` with `Retry-After` header
- Rate limit headers returned on every response: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### Request Correlation

Every API response includes a `X-Request-ID` header (UUID). This ID is propagated to all downstream services (AI service, audit log, background jobs) for distributed tracing.

### API Versioning

The spec uses `/api/v1/`. Breaking changes will introduce `/api/v2/` with a minimum 6-month deprecation window for v1 endpoints. Deprecated endpoints return a `Sunset` header.

### Soft-Delete Pattern

All entities except immutable audit logs follow a consistent soft-delete pattern:
- **Status-based entities** (candidates, requisitions, shortlists, placements): soft-delete via status transition to a terminal state (archived, closed, terminated). Records with terminal statuses are excluded from default queries but accessible via explicit filters.
- **Non-status entities** (sourcing_lists, outreach_templates, outreach_sequences): use an `is_active BOOLEAN DEFAULT true` column. API DELETE endpoints set `is_active = false` instead of removing the row. Hard-delete only after retention period expires.

This ensures data preservation for audit compliance and avoids cascading FK issues.

---

## 4.1.1 Multi-Tenant Platform

### User Story
As an Agency Admin, I want to create and manage my agency's tenant workspace with isolated data, role-based access, and audit logging so that my recruiters and clients operate in a secure, compliant environment.

### Data Model

**`organizations`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| name | VARCHAR(255) | NOT NULL |
| slug | VARCHAR(100) | NOT NULL, UNIQUE (globally unique) |
| kms_key_id | VARCHAR(255) | nullable (enterprise tenants) |
| data_region | VARCHAR(10) | NOT NULL, CHECK (IN ('us','uk','eu')) (v1 constraint — expand via lookup table post-v1) |
| retention_days | INT | NOT NULL, DEFAULT 365 |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**`platform_users`** (platform-level — SuperAdmin only)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'superadmin' |
| full_name | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Note: SuperAdmin is a platform-level role outside tenant scope. SuperAdmins manage tenant provisioning and platform configuration but do not appear in tenant user lists.

**`users`** (tenant-scoped)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| email | VARCHAR(255) | NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| role | VARCHAR(20) | NOT NULL, CHECK (IN ('admin','recruiter','client_readonly')) |
| full_name | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| last_login_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Unique: `UNIQUE (organization_id, email)` where `is_active = true`. Partial unique index: `CREATE UNIQUE INDEX idx_users_org_active_email ON users(organization_id, email) WHERE is_active = true;`

**`client_contacts`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| client_name | VARCHAR(255) | NOT NULL |
| contact_name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(50) | nullable |
| role | VARCHAR(100) | nullable |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Unique: `UNIQUE (organization_id, email)`

**`audit_logs`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| user_id | UUID | FK -> users.id, nullable |
| event_type | VARCHAR(50) | NOT NULL (user_created, user_role_changed, user_deactivated, login, logout, password_reset, invitation_sent, candidate_created, candidate_status_changed, placement_created, placement_fee_changed, ai_rank_override, shortlist_approved, portal_link_generated, portal_access, export_generated, report_exported) |
| resource_type | VARCHAR(50) | NOT NULL (user, candidate, requisition, shortlist, placement, portal_session, report) |
| resource_id | UUID | nullable |
| metadata | JSONB | nullable (event-specific payload, no PII) |
| ip_address | INET | nullable |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Retention: 3 years (configurable per tenant via organizations.retention_days). Archive strategy: monthly partition by created_at.

**RLS Policy (PostgreSQL):** Applied to every tenant-scoped table in the schema (candidates, candidate_skills, candidate_documents, candidate_timeline, requisitions, requisition_skills, shortlists, shortlist_candidates, interviews, placements, sourcing_lists, sourcing_list_candidates, outreach_templates, outreach_sequences, sequence_steps, activities, client_portal_sessions, client_feedback, search_log, report_definitions, audit_logs):

```sql
-- Template policy — applied per table with table_name substituted
CREATE POLICY tenant_isolation ON {table_name}
  USING (organization_id = current_setting('app.organization_id')::UUID);

-- Exception: platform_users table has no RLS (platform-level)
-- Exception: organizations table uses id = current_setting('app.organization_id')::UUID
CREATE POLICY org_isolation ON organizations
  USING (id = current_setting('app.organization_id')::UUID);
```

The `app.organization_id` session variable is set via a middleware hook executed on every authenticated request, reading the `org_id` claim from the JWT. Implemented as a per-request `SET LOCAL` in the database connection pooler.

**S3 Storage Layout:**
```
s3://{tenant-bucket}/{organization_id}/documents/{candidate_id}/{file_uuid}.pdf
s3://{tenant-bucket}/{organization_id}/uploads/{recruiter_id}/{file_uuid}.pdf
```

### API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/organizations | SuperAdmin | Provision new tenant |
| GET | /api/v1/organizations/:id | Admin | Get tenant details |
| PUT | /api/v1/organizations/:id | Admin | Update tenant config |
| GET | /api/v1/users | Admin | List users in tenant |
| POST | /api/v1/users/invite | Admin | Send invitation email — user sets password via link |
| POST | /api/v1/users/resend-invite/:id | Admin | Re-send invitation email |
| PUT | /api/v1/users/:id | Admin | Update user role/status |
| DELETE | /api/v1/users/:id | Admin | Deactivate user |
| POST | /api/v1/auth/login | Public | Email + password → JWT (access + refresh) |
| POST | /api/v1/auth/refresh | Public | Refresh token → new access token |
| POST | /api/v1/auth/forgot-password | Public | Email → reset link sent |
| POST | /api/v1/auth/reset-password | Public | Reset token → new password |
| POST | /api/v1/client-contacts | Admin | Create client contact |
| GET | /api/v1/client-contacts | Admin | List client contacts |
| PUT | /api/v1/client-contacts/:id | Admin | Update client contact |
| DELETE | /api/v1/client-contacts/:id | Admin | Deactivate client contact |

### JWT Token Structure

Access token:
```json
{
  "sub": "user-uuid",
  "org_id": "org-uuid",
  "role": "recruiter",
  "iat": 1680000000,
  "exp": 1680086400
}
```

- Access token TTL: 24 hours
- Refresh token TTL: 30 days (rotated on use; old refresh token invalidated)
- Revocation: on password change, role change, user deactivation — all active sessions for that user are invalidated by incrementing a `token_version` counter on the user record

### UI Components
- **Admin Console:** Tenant settings page with data region selector, retention policy config, encryption key status
- **User Management Table:** List of users with role badges, status indicators, invite resend
- **Role Badge:** Color-coded chip (Admin=purple, Recruiter=blue, Client=gray)

### Business Logic
- Password hashing via bcrypt (cost 12)
- Session tokens via JWT with 24h expiry, refresh token with 30d expiry
- Every query must pass `organization_id` via session context — enforced at middleware layer via `SET LOCAL app.organization_id = :org_id`
- KMS key rotation triggers re-encryption of new objects only (existing objects retain prior key)
- User invitation flow: Admin sends invite → email with magic link (48h TTL) → user clicks → sets password → account activated
- Password reset flow: User requests reset → email with reset token (1h TTL) → user submits new password → all sessions invalidated
- Tenant provisioning: SuperAdmin creates organization record → platform sends welcome email with admin account setup link — no self-serve tenant creation in v1

### Integration Points
- Auth0/Okta SSO (roadmap, not v1)
- Audit log service (all user CRUD events, login events, invitation events, password resets)

### Acceptance Criteria
1. Admin can create a tenant with a unique slug and region
2. Users in Tenant A cannot access records belonging to Tenant B (verified via RLS)
3. Deactivating a user immediately revokes all active sessions (token_version check on every request)
4. Audit log contains a timestamped entry for every user creation, role change, and deactivation
5. Invitation link expires after 48h; using an expired link shows "Link expired — contact your admin"
6. Password reset link is single-use and expires after 1 hour

---

## 4.1.2 Candidate Management

### User Story
As a Sourcer, I want to create candidate profiles from resume uploads (PDF, DOCX, TXT), enrich them with structured data, detect duplicates, store documents, and track their activity timeline so that I have a complete, deduplicated view of every candidate.

### Data Model

**`candidates`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| first_name | VARCHAR(255) | NOT NULL |
| last_name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | nullable |
| phone | VARCHAR(50) | nullable |
| current_title | VARCHAR(255) | nullable |
| current_employer | VARCHAR(255) | nullable |
| location | VARCHAR(255) | nullable |
| salary_expectation_min | INT | nullable |
| salary_expectation_max | INT | nullable |
| visa_status | VARCHAR(50) | nullable |
| notice_period_days | INT | nullable |
| source | VARCHAR(100) | NOT NULL (linkedin, dribbble, github, referral, agency_db, manual) |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'sourced' |
| owner_id | UUID | FK -> users.id, nullable |
| ai_summary | TEXT | nullable (generated by 4.2.2) |
| ai_summary_generated_at | TIMESTAMPTZ | nullable |
| is_ai_summary_edited | BOOLEAN | DEFAULT false (true when recruiter manually edits AI summary) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Unique: `CREATE UNIQUE INDEX idx_candidates_unique_email ON candidates(organization_id, email) WHERE email IS NOT NULL;`

Status CHECK constraint removed in favor of state machine enforcement at application layer (see Candidate Status State Machine below).

**`candidate_skills`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| candidate_id | UUID | FK -> candidates.id, ON DELETE CASCADE |
| skill_name | VARCHAR(100) | NOT NULL |
| proficiency | VARCHAR(20) | nullable (beginner, proficient, advanced, expert) |
| years_experience | DECIMAL(4,1) | nullable |

Unique: `UNIQUE (candidate_id, skill_name)`

**`candidate_documents`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| candidate_id | UUID | FK -> candidates.id, ON DELETE CASCADE |
| document_type | VARCHAR(50) | NOT NULL (resume, cover_letter, certification, other) |
| file_name | VARCHAR(255) | NOT NULL |
| file_size_bytes | INT | NOT NULL |
| s3_key | VARCHAR(500) | NOT NULL |
| uploaded_by | UUID | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**`candidate_timeline`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| candidate_id | UUID | FK -> candidates.id, ON DELETE CASCADE |
| event_type | VARCHAR(50) | NOT NULL, CHECK (IN ('profile_created','resume_uploaded','status_changed','ai_summary_generated','document_added','candidate_merged','candidate_archived','outreach_activity')) |
| description | TEXT | NOT NULL |
| metadata | JSONB | nullable |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Auto-generated events: profile_created, resume_uploaded, status_changed, ai_summary_generated, document_added, candidate_merged, candidate_archived. Outreach activities are mirrored from the `activities` table as event_type='outreach_activity'. The `activities` table (4.1.5) tracks recruiter CRM events (outreach, notes, calls) and candidate-scoped activities appear on the timeline with a reference link to the activity ID. The two tables serve different query patterns: `candidate_timeline` for a full chronological view of everything that happened to/with a candidate, `activities` for CRM-specific outreach tracking.

### Candidate Status State Machine

```
sourced ──→ in_review ──→ submitted ──→ interviewing ──→ placed
   │             │             │               │             │
   └──→ rejected ←┴───────────┴───────────────┴─────────────┴──→ archived
                                                                   ↑
                                                              (any state)
```

| Transition | Who Can Trigger | Reason Required? | Side Effects |
|------------|----------------|------------------|--------------|
| sourced → in_review | Owner, Admin | No | Timeline event |
| in_review → submitted | Owner, Admin | No | Timeline event |
| in_review → rejected | Owner, Admin | Yes | Timeline event; recycle candidate |
| submitted → interviewing | Admin | No | Timeline event; notify assigned recruiter |
| submitted → rejected | Admin | Yes | Timeline event; recycle |
| submitted → in_review | Admin | Yes ("Returned for more sourcing") | Timeline event |
| interviewing → placed | Admin | No | Timeline event; create placement record |
| interviewing → rejected | Admin | Yes | Timeline event |
| interviewing → in_review | Admin | Yes ("Client wants to revisit") | Timeline event |
| placed → archived | Admin | Yes ("Guarantee period ended") | Timeline event |
| any → rejected | Admin | Yes | Timeline event; recycle |
| any → archived | Admin | Yes | Timeline event; hard-delete eligible after retention period |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/candidates | Create candidate manually |
| POST | /api/v1/candidates/upload | Upload resume + create candidate (multipart) |
| GET | /api/v1/candidates | List/search candidates (paginated, filtered) |
| GET | /api/v1/candidates/:id | Get candidate with skills, documents, timeline |
| PUT | /api/v1/candidates/:id | Update candidate fields |
| PATCH | /api/v1/candidates/:id/status | Change status with reason (validated against state machine) |
| DELETE | /api/v1/candidates/:id | Soft-delete (status=archived) |
| GET | /api/v1/candidates/:id/documents | List documents |
| POST | /api/v1/candidates/:id/documents | Upload document |
| GET | /api/v1/candidates/:id/timeline | Get activity timeline (paginated) |
| POST | /api/v1/candidates/dedup-check | Check duplicates by email/phone |

### UI Components
- **Candidate Grid:** Card view with avatar, name, role, AI summary snippet, skill tags, source icon, date
- **Candidate Detail Panel:** Split into tabs — Profile, Documents, Timeline. Profile shows AI summary box, skills matrix, info rows
- **Upload Dropzone:** Drag-and-drop for PDF/DOCX/TXT with progress indicator
- **Dedup Dialog:** Modal showing matched candidates when duplicate detected on upload, with "Merge" / "Keep Separate" actions
- **Status Badge:** Color-coded (sourced=blue, review=amber, submitted=green, placed=purple, rejected=red)

### Business Logic
- Resume upload triggers a background job: extract text → parse (4.2.1) → create candidate → check duplicates
- Duplicate detection: exact email match = strong duplicate; phone + name similarity (Jaro-Winkler distance > 0.9) = weak duplicate
- Timeline events auto-generated for: profile created, resume uploaded, status changed, AI summary generated, document added
- Soft-delete preserves data for audit compliance; hard-delete only after retention period expires
- Ownership: `owner_id` set by recruiter who creates the candidate. Ownership transfer via PUT endpoint with reason. When owner is deactivated, their candidates become unassigned (owner_id=null)

### Integration Points
- Resume Parsing Service (4.2.1) — called asynchronously after upload
- AI Summary Service (4.2.2) — regenerated on profile data changes
- Dedup engine compares against existing candidates within same organization

### Acceptance Criteria
1. Uploading a PDF resume creates a candidate profile with extracted structured data within 5 seconds
2. System detects and alerts on duplicate email during upload with Jaro-Winkler name match
3. Timeline shows chronological events with correct timestamps
4. Documents are stored in tenant-isolated S3 and retrievable via API
5. Searching candidates by name, skill, or source returns results within 200ms
6. Invalid status transitions (e.g., sourced → placed) return 422 with allowed transitions in error message

---

## 4.1.3 Job & Requisition Management

### User Story
As an Account Manager, I want to create job requisitions from client intake, capture structured requirements, and track each requisition through its lifecycle stages so that my team knows what we're hiring for and where each search stands.

### Data Model

**`requisitions`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| client_contact_id | UUID | FK -> client_contacts.id, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| location | VARCHAR(255) | nullable |
| is_remote | BOOLEAN | DEFAULT false |
| salary_min | INT | nullable |
| salary_max | INT | nullable |
| currency | VARCHAR(3) | DEFAULT 'USD' |
| visa_sponsorship | VARCHAR(100) | nullable |
| urgency | VARCHAR(20) | NOT NULL, DEFAULT 'standard', CHECK (IN ('urgent','standard','low')) |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'open', CHECK (IN ('open','in_progress','submitted','filled','closed')) |
| deal_fee_percent | DECIMAL(5,2) | nullable |
| deal_guarantee_days | INT | nullable |
| positions_count | INT | NOT NULL, DEFAULT 1 |
| description | TEXT | nullable |
| posted_at | TIMESTAMPTZ | DEFAULT now() |
| filled_at | TIMESTAMPTZ | nullable |
| closed_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

`client_name` is derived from `client_contacts.client_name` — not stored as a separate string.

**`requisition_skills`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| requisition_id | UUID | FK -> requisitions.id, ON DELETE CASCADE |
| skill_name | VARCHAR(100) | NOT NULL |
| is_required | BOOLEAN | DEFAULT true |
| min_years | DECIMAL(3,1) | nullable |

**`requisition_stages`** (configurable per client)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| stage_name | VARCHAR(100) | NOT NULL |
| stage_order | INT | NOT NULL |
| is_default | BOOLEAN | DEFAULT false |

Requisition status transitions:
```
open → in_progress → submitted → filled
  ↓         ↓            ↓
closed    closed       closed
```

| Transition | Who Can Trigger | Reason Required? | Side Effects |
|------------|----------------|------------------|--------------|
| open → in_progress | Admin | No | Timeline event |
| in_progress → submitted | Admin | No | Requires at least one candidate shortlist submitted |
| submitted → filled | Admin | Yes ("candidate_id": UUID) | Sets filled_at; auto-closes remaining positions |
| submitted → in_progress | Admin | Yes ("Need more candidates") | Timeline event |
| any → closed | Admin | Yes (filled, cancelled, on_hold) | Sets closed_at; stops AI match computation |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/requisitions | Create requisition |
| GET | /api/v1/requisitions | List with filters (status, client_contact_id, urgency) |
| GET | /api/v1/requisitions/:id | Get full details with skills, client contact, pipeline counts |
| PUT | /api/v1/requisitions/:id | Update |
| PATCH | /api/v1/requisitions/:id/status | Transition status (validated) |
| POST | /api/v1/requisitions/:id/skills | Add skill requirement |
| DELETE | /api/v1/requisitions/:id/skills/:skillId | Remove skill |
| GET | /api/v1/requisition-stages | List stages (scoped to org) |
| POST | /api/v1/requisition-stages | Create stage |
| PUT | /api/v1/requisition-stages/:id | Update stage |
| DELETE | /api/v1/requisition-stages/:id | Delete stage (not allowed if in use by active requisitions) |
| POST | /api/v1/requisitions/:id/reorder-stages | Reorder stages for this requisition |

### Visibility Rules
- Admin: full visibility into all requisitions in the tenant
- Recruiter: can see all requisitions in the tenant (read-only for non-owned), can edit only requisitions they are assigned to (via `owner_id` or team membership)
- Client: no direct access — sees only via client portal (4.1.6)

### UI Components
- **Requisition List:** Card view showing title, client name, status badge, urgency icon, salary, skills, pipeline counts
- **Intake Form:** Structured form with sections — Role Details, Requirements, Compensation, Deal Terms
- **Status Timeline:** Visual progress bar on detail page showing current stage and history
- **Pipeline Mini-View:** Embedded horizontal bar chart showing candidate counts at each stage for this requisition

### Business Logic
- Status transitions follow the rules above; invalid transitions return 422 with allowed options
- Closing a requisition requires a reason (filled, cancelled, on_hold)
- Pipeline counts computed via JOIN on submissions grouped by stage
- AI match score (4.2.4) computed only when status is 'open' or 'in_progress'

### Integration Points
- Client Contacts (4.1.1) provide the client reference instead of a plain string
- Submission pipeline (4.1.4) links candidates to requisitions
- AI Match (4.2.4) uses requisition skills as comparison target
- Client Portal (4.1.6) surfaces requisition progress

### Acceptance Criteria
1. Creating a requisition with required skills populates the intake form correctly
2. Status transitions follow the defined lifecycle; invalid transitions are rejected with 422
3. Pipeline mini-view on the requisition card shows accurate candidate counts
4. Closing a requisition without a reason is blocked
5. Requisition skills can be managed independently (add/remove without recreating the requisition)
6. Client name is resolved from the client_contacts table, not stored as free text

---

## 4.1.4 Submission & Workflow Management

### User Story
As a Recruiter, I want to create shortlists of candidates for a job, submit them through an approval workflow, track interview stages, manage offers and placements, and log fees so that the entire placement lifecycle is managed in one place.

### Data Model

**`shortlists`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| requisition_id | UUID | FK -> requisitions.id, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'draft', CHECK (IN ('draft','pending_approval','approved','submitted','rejected')) |
| submitted_at | TIMESTAMPTZ | nullable |
| submitted_by | UUID | FK -> users.id |
| approved_at | TIMESTAMPTZ | nullable |
| approved_by | UUID | FK -> users.id |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Multiple shortlists per requisition are allowed (e.g., one for senior candidates, one for junior candidates). Each shortlist is submitted independently.

**`shortlist_candidates`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| shortlist_id | UUID | FK -> shortlists.id, ON DELETE CASCADE |
| candidate_id | UUID | FK -> candidates.id |
| ai_rank | INT | nullable (populated by 4.2.4 AI Match on demand) |
| recruiter_rank | INT | nullable (recruiter override) |
| override_reason | TEXT | nullable (required if recruiter_rank != ai_rank) |
| status | VARCHAR(30) | DEFAULT 'pending', CHECK (IN ('pending','approved','rejected','withdrawn')) |

`ai_rank` is populated when the recruiter triggers `POST /api/v1/requisitions/:id/rank` (AI Match 4.2.4). It is not auto-populated on shortlist creation.

**`interviews`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| shortlist_candidate_id | UUID | FK -> shortlist_candidates.id |
| stage | VARCHAR(100) | NOT NULL (should reference requisition_stages.id in v2; free-text in v1) |
| scheduled_at | TIMESTAMPTZ | nullable |
| feedback | TEXT | nullable |
| feedback_by | UUID | FK -> users.id |
| outcome | VARCHAR(20) | nullable ('advance','reject','hold') |

Interview scheduling is external (email/calendar tool) — the system only logs the scheduled time and outcome.

**`placements`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| shortlist_candidate_id | UUID | FK -> shortlist_candidates.id, UNIQUE |
| start_date | DATE | NOT NULL |
| salary | INT | NOT NULL |
| fee_percentage | DECIMAL(5,2) | NOT NULL |
| fee_amount | DECIMAL(10,2) | NOT NULL (computed — see below) |
| guarantee_until | DATE | nullable |
| commission_owner_id | UUID | FK -> users.id |
| status | VARCHAR(20) | DEFAULT 'active', CHECK (IN ('active','guarantee_period','completed','terminated')) |

**Fee computation:** `fee_amount = salary * fee_percentage / 100`. Computed by application logic on write (insert or update of salary/fee_percentage). Not implemented as a generated column — application computes and stores the value. Recalculated whenever `salary` or `fee_percentage` changes.

**Recycled candidates:** When a candidate is rejected at any stage, their `shortlist_candidates.status` is set to `rejected`. The candidate record itself is not changed. A "recycle pool" is represented by querying for candidates with `status = 'rejected'` across any shortlist, with a `recycled_at` computed field. No separate `recycled_candidates` table in v1.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/requisitions/:id/shortlists | Create shortlist |
| GET | /api/v1/requisitions/:id/shortlists | List shortlists for a requisition |
| POST | /api/v1/shortlists/:id/candidates | Add candidate to shortlist |
| DELETE | /api/v1/shortlists/:id/candidates/:cid | Remove candidate from shortlist |
| POST | /api/v1/shortlists/:id/approve | Approve shortlist (human gate) |
| POST | /api/v1/shortlists/:id/submit | Submit to client (status → submitted, triggers portal link) |
| PUT | /api/v1/shortlist-candidates/:id/rank | Override AI rank (requires reason) |
| POST | /api/v1/shortlist-candidates/:id/interviews | Log interview |
| POST | /api/v1/shortlist-candidates/:id/placement | Create placement |
| GET | /api/v1/requisitions/:id/pipeline | Get pipeline state for all candidates |
| GET | /api/v1/recycle | List recycled candidates (rejected shortlist candidates) |

### UI Components
- **Kanban Pipeline:** 4-6 columns (Sourced → In Review → Submitted → Interview → Offer → Placed) with draggable candidate cards
- **Shortlist Builder:** Two-panel view with available candidates (left) and shortlist (right), AI-ranked by default
- **Approval Gate:** Modal showing AI rank vs recruiter rank with diff highlighting; override reason textarea required if ranks differ
- **Placement Form:** Fee calculator with auto-computed commission based on fee percentage

### Business Logic
- Shortlist export to client triggers status=submitted and generates magic link (4.1.6)
- If recruiter_rank != ai_rank, override_reason is mandatory (EU AI Act Art. 14 compliance)
- Any candidate rejected at any stage enters the "recycle" pool — recruiter can associate with other requisitions via a new shortlist
- Placement fee_amount = salary * fee_percentage / 100, recalculated on salary or fee_percentage change
- Max candidates per shortlist: 25 (configurable per tenant)
- Post-approval modification: adding candidates to an approved shortlist sets its status back to `draft`, requiring re-approval

### Integration Points
- Client Portal (4.1.6) receives submitted shortlists
- AI Match (4.2.4) populates initial ai_rank on demand
- Candidate Timeline gets events for each status change

### Acceptance Criteria
1. Recruiter can add candidates to a shortlist and reorder them manually
2. Approving a shortlist without an override reason when ranks differ is blocked with 422
3. Client can view the submitted shortlist via magic link within 60 seconds of submission
4. Placement fee auto-calculates on salary entry (fee_amount = salary * fee_percentage / 100)
5. Rejected candidates appear in the recycle pool query within 5 seconds of rejection
6. Adding a candidate to an approved shortlist resets it to draft status

---

## 4.1.5 Recruiter CRM & Outreach

### User Story
As a Sourcer, I want to create sourcing lists, manage outreach sequences with templates, track all communications and activities, and view relationship history so that I can scale candidate engagement without losing context.

### Data Model

**`sourcing_lists`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| name | VARCHAR(255) | NOT NULL |
| description | TEXT | nullable |
| created_by | UUID | FK -> users.id |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**`sourcing_list_candidates`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| sourcing_list_id | UUID | FK -> sourcing_lists.id, ON DELETE CASCADE |
| candidate_id | UUID | FK -> candidates.id |
| notes | TEXT | nullable |
| added_at | TIMESTAMPTZ | DEFAULT now() |

**`outreach_templates`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| name | VARCHAR(255) | NOT NULL |
| subject | VARCHAR(500) | nullable (email subject) |
| body | TEXT | NOT NULL |
| channel | VARCHAR(20) | NOT NULL (email, linkedin, sms) |
| variables | JSONB | nullable (list of template variable names) |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**`outreach_sequences`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| name | VARCHAR(255) | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**`sequence_steps`** (replaces JSONB `steps` on `outreach_sequences`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id, NOT NULL |
| sequence_id | UUID | FK -> outreach_sequences.id, ON DELETE CASCADE |
| template_id | UUID | FK -> outreach_templates.id |
| step_order | INT | NOT NULL |
| delay_hours | INT | NOT NULL |
| channel | VARCHAR(20) | NOT NULL |

Unique: `UNIQUE (sequence_id, step_order)`

**`activities`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| candidate_id | UUID | FK -> candidates.id, nullable |
| client_contact_id | UUID | FK -> client_contacts.id, nullable |
| activity_type | VARCHAR(50) | NOT NULL (email_sent, email_opened, call, follow_up, meeting, note, opt_out) |
| description | TEXT | NOT NULL |
| metadata | JSONB | nullable |
| performed_by | UUID | FK -> users.id |
| performed_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

Relationship to `candidate_timeline`: The `activities` table tracks recruiter CRM events (outreach, notes, calls). Candidate-scoped activities are also mirrored to `candidate_timeline` as `event_type = 'outreach_activity'` with a reference to the activity ID. This ensures the candidate timeline provides a complete chronological view of everything related to a candidate, while `activities` provides CRM-specific filtering and analytics.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/sourcing-lists | List sourcing lists |
| POST | /api/v1/sourcing-lists | Create sourcing list |
| PUT | /api/v1/sourcing-lists/:id | Update sourcing list |
| DELETE | /api/v1/sourcing-lists/:id | Delete sourcing list |
| POST | /api/v1/sourcing-lists/:id/candidates | Add candidate to list |
| DELETE | /api/v1/sourcing-lists/:id/candidates/:cid | Remove candidate from list |
| GET | /api/v1/outreach-templates | List templates |
| POST | /api/v1/outreach-templates | Create template |
| PUT | /api/v1/outreach-templates/:id | Update template |
| DELETE | /api/v1/outreach-templates/:id | Delete template |
| GET | /api/v1/outreach-sequences | List sequences |
| POST | /api/v1/outreach-sequences | Create sequence |
| PUT | /api/v1/outreach-sequences/:id | Update sequence |
| DELETE | /api/v1/outreach-sequences/:id | Delete sequence |
| POST | /api/v1/outreach-sequences/:id/steps | Add step to sequence |
| PUT | /api/v1/outreach-sequences/:id/steps/:stepId | Update step |
| DELETE | /api/v1/outreach-sequences/:id/steps/:stepId | Delete step |
| POST | /api/v1/outreach-sequences/:id/reorder-steps | Reorder steps |
| POST | /api/v1/outreach/draft | Generate AI draft (via 4.2.5) |
| POST | /api/v1/outreach/send | Send outreach (logs activity, checks opt-out) |
| GET | /api/v1/candidates/:id/activities | Get activity history for candidate |

### UI Components
- **Sourcing List Panel:** Sidebar accordion with lists; drag candidate from search results onto list
- **Template Editor:** Rich text editor with variable insertion (`{{candidate_name}}`, `{{job_title}}`)
- **Sequence Builder:** Visual step list with drag-to-reorder, delay configuration per step
- **Activity Feed:** Chronological log on candidate detail page with icon per activity type

### Business Logic
- Sending outreach creates an Activity record and a corresponding candidate_timeline entry automatically
- Before sending, the system checks if the candidate has an `opt_out` activity — if so, the send is blocked with a 403 response
- Opt-out handling: recipients can reply with STOP; this creates an `opt_out` activity and blocks future outreach
- AI draft (4.2.5) populates template variables when generating personalized messages
- Sequence automation is manual-trigger (not auto-send) in v1 — recruiter reviews each step before sending
- Activity feed is read-only; no editing or deleting historical activities
- Outreach rate limiting: max 3 outbound messages per candidate per day (prevents spam)
- Email deliverability tracking (bounces, opens, clicks) is deferred to v2

### Integration Points
- AI Outreach (4.2.5) generates drafts and suggests sequences
- Candidate profile (4.1.2) links activities to candidates
- Client Contacts (4.1.1) provides the client_contact reference

### Acceptance Criteria
1. Recruiter can create a sourcing list and add candidates from search results
2. Template variables are rendered correctly when previewed
3. Sending an outreach creates a timestamped activity on the candidate's timeline
4. Activity feed shows complete history for a candidate across all outreach attempts
5. Sending outreach to an opted-out candidate is blocked with 403
6. Deleting a template that is referenced by a sequence step returns 409 (integrity protected)

---

## 4.1.6 Client Portal (Read-Only)

### User Story
As a Client hiring manager, I want to receive a secure link to review submitted candidates, read AI-generated summaries, provide feedback, and track progress so that I can evaluate candidates without logging into yet another system.

### Data Model

**`client_portal_sessions`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| client_contact_id | UUID | FK -> client_contacts.id |
| created_by | UUID | FK -> users.id |
| email | VARCHAR(255) | NOT NULL |
| client_name | VARCHAR(255) | nullable |
| requisition_id | UUID | FK -> requisitions.id |
| token | VARCHAR(255) | UNIQUE, NOT NULL |
| otp_code | VARCHAR(6) | nullable |
| otp_expires_at | TIMESTAMPTZ | nullable |
| last_accessed_at | TIMESTAMPTZ | nullable |
| expires_at | TIMESTAMPTZ | NOT NULL (magic link TTL: 7 days) |
| invalidated_at | TIMESTAMPTZ | nullable (set when recruiter revokes access) |
| created_at | TIMESTAMPTZ | DEFAULT now() |

`client_contact_id` links to the client_contacts table. The `email` and `client_name` fields are denormalized for audit purposes (the contact may change after the link is generated).

**`client_feedback`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| shortlist_candidate_id | UUID | FK -> shortlist_candidates.id |
| client_portal_session_id | UUID | FK -> client_portal_sessions.id |
| decision | VARCHAR(20) | NOT NULL (approve, reject, maybe) |
| comment | TEXT | nullable |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**`portal_access_log`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| client_portal_session_id | UUID | FK -> client_portal_sessions.id |
| action | VARCHAR(50) | NOT NULL (view_submissions, view_candidate, submit_feedback) |
| candidate_id | UUID | FK -> candidates.id, nullable |
| ip_address | INET | nullable |
| user_agent | TEXT | nullable |
| created_at | TIMESTAMPTZ | DEFAULT now() |

This log enables recruiters to see which clients are actively reviewing candidates and which submissions got the most attention.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/client-portal/generate-link | Generate magic link for client |
| POST | /api/v1/client-portal/revoke/:sessionId | Invalidate all sessions for a client (recruiter action) |
| GET | /api/v1/client-portal/verify?token= | Verify token, show OTP screen |
| POST | /api/v1/client-portal/verify-otp | Verify OTP, issue session |
| GET | /api/v1/client-portal/submissions | List submitted candidates for this session |
| GET | /api/v1/client-portal/submissions/:id | View candidate submission with AI summary |
| POST | /api/v1/client-portal/feedback | Submit feedback on candidate |
| GET | /api/v1/client-portal/access-log | View access log (recruiter-side) |

### UI Components
- **Magic Link Email:** Branded template with "View Submission" button, expiry notice, security footer
- **OTP Verification:** Simple code input (6 digits), resend timer (30s)
- **Submission Review:** Card layout showing candidate name, role, AI-generated summary, skills, availability
- **Feedback Widget:** Three-button decision (Approve / Maybe / Pass) with optional comment textarea
- **Progress Bar:** Top of portal showing stages and where this requisition stands

### Business Logic
- Magic link expires after 7 days (independent of OTP expiry — a valid link can generate a new OTP if the previous one expired)
- OTP is single-use, expires after 10 minutes. If OTP expires, the client can click "Resend code" to get a new OTP (max 3 resends per magic link)
- Failed OTP attempts: 5 max, then link invalidated. Shows "Too many failed attempts — contact your recruiter for a new link" (not "wrong code" specifically, to avoid enumeration attacks)
- Session is scoped to a single requisition — client sees only candidates submitted to that job
- Portal is read-only: no document download, no candidate contact info, no external links
- Feedback is pushed back to the recruiter's pipeline view in real-time via WebSocket event (subscription: `ws://host/ws/pipeline/{requisition_id}`). WebSocket reconnection uses exponential backoff (1s, 2s, 4s). If WebSocket unavailable, feedback is available on next page refresh via polling.
- Report exports also use the same WebSocket channel — recruiter receives a `report_ready` event with the export download URL
- Recruiter can revoke all portal sessions for a client via `POST /api/v1/client-portal/revoke/:sessionId`

### Integration Points
- Client Contacts (4.1.1) provides the client reference
- Shortlist (4.1.4) triggers portal link generation when submitted
- Candidate AI summary (4.2.2) is rendered in the submission card
- Email delivery via SendGrid / SES transactional API

### Acceptance Criteria
1. Generating a magic link sends an email that renders correctly on desktop and mobile
2. OTP verification succeeds within 10 minutes; expired OTP shows correct error message
3. Client can see submitted candidates with AI summaries but not contact details
4. Submitting feedback immediately updates the recruiter's pipeline view
5. Exceeding 5 failed OTP attempts renders the link unusable
6. Revoking portal access immediately blocks all active sessions for that client
7. Portal access log captures client view and feedback actions with timestamps

---

## 4.1.7 Search & Reporting

### User Story
As a Recruiter, I want to search across candidates and jobs by multiple criteria, view pipeline health dashboards, and export reports so that I can find information quickly and demonstrate progress to clients and management.

### Data Model

**`search_log`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| user_id | UUID | FK -> users.id |
| query | TEXT | NOT NULL |
| filters | JSONB | nullable |
| result_count | INT | NOT NULL |
| executed_at | TIMESTAMPTZ | DEFAULT now() |

**`report_definitions`**
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| organization_id | UUID | FK -> organizations.id |
| name | VARCHAR(255) | NOT NULL |
| type | VARCHAR(50) | NOT NULL (pipeline_health, submissions, recruiter_productivity, time_to_fill) |
| config | JSONB | nullable |
| created_by | UUID | FK -> users.id |
| created_at | TIMESTAMPTZ | DEFAULT now() |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/search/candidates | Search candidates (q, skill, location, status, source, salary, visa) |
| GET | /api/v1/search/requisitions | Search requisitions (q, status, client_contact_id, urgency, skill) |
| GET | /api/v1/dashboards/pipeline | Pipeline health summary (counts by stage, this week vs last week) |
| GET | /api/v1/dashboards/submissions | Submission metrics (volume, response rates, time-to-submit) |
| GET | /api/v1/dashboards/recruiter | Recruiter productivity (candidates processed, submissions, placements) |
| POST | /api/v1/reports/:type/export | Request report export (async); returns export_id |
| GET | /api/v1/reports/exports/:exportId | Download generated report (when ready) |

### Search Query Parameters
```
GET /api/v1/search/candidates?q=react&skills=TypeScript,Node.js&location=SF
  &status=sourced,in_review&source=linkedin&salary_min=100000&cursor=...&limit=50
```

URL length limit: if the combined query string exceeds 4,000 characters, clients should use `POST /api/v1/search/candidates` with a JSON body instead. The GET endpoint returns 414 (URI Too Long) when the limit is exceeded, with the response body containing the POST endpoint alternative and schema.

### Search Ranking
Search results are ranked by a combination of:
1. Full-text match score (ts_rank from PostgreSQL `tsvector` on name, title, skills)
2. Recency boost: candidates updated in the last 7 days get +0.2 score multiplier
3. Owner preference: candidates owned by the searching user get +0.1 score multiplier

The combined score is `ts_rank * recency_boost * owner_boost`. Results are ordered by combined score descending.

### UI Components
- **Global Search Bar:** Top-bar search with typeahead, scope toggle (Candidates / Jobs / All)
- **Faceted Filters:** Sidebar panel with checkbox groups for status, source, skills — results update on selection
- **Dashboard Widgets:** Draggable card grid (pipeline funnel chart, submission trend line, recruiter leaderboard)
- **Export Button:** Download dropdown (CSV, PDF) with date range picker

### Business Logic
- Search uses PostgreSQL full-text search (tsvector on name, title, skills) with GIN index
- Filters are AND-combined; within a filter group values are OR-combined
- Dashboard metrics are materialized views refreshed every 15 minutes via a cron job (`pg_cron` or application scheduler). During refresh, the old materialized view remains available (no downtime). If a refresh fails, the previous data is retained and an admin alert is sent.
- Materialized views defined:
  - `mv_pipeline_counts`: candidate counts per stage per requisition (sources: shortlists, shortlist_candidates)
  - `mv_submission_metrics`: weekly submission volume, response rates, time-to-submit (sources: shortlists, client_feedback)
  - `mv_recruiter_productivity`: per-recruiter counts of candidates processed, submissions sent, placements made (sources: candidates, shortlists, placements)
- Report exports are generated asynchronously (queued job); for datasets > 1000 rows, export uses streaming pagination
- On export completion, the user receives a notification via WebSocket (`report_ready` event on the user's notification channel `ws://host/ws/notifications/{user_id}`) with the download URL. Alternatively, the client can poll `GET /api/v1/reports/exports/:exportId`.
- Search results are always scoped to the user's organization (RLS enforced)
- Zero-result queries are logged in `search_log` for product analytics

### Integration Points
- All CRUD operations across candidates, jobs, and submissions feed the search index
- Dashboard materialized views depend on submissions, interviews, and placements tables

### Acceptance Criteria
1. Searching by skill name returns all candidates with that skill, ordered by match relevance
2. Applying multiple filters narrows results correctly (AND across filter groups)
3. Pipeline dashboard shows correct counts matching the kanban state
4. CSV export contains the same data visible in the search results and streams correctly for 10,000+ rows
5. Search results are scoped to the user's tenant and never leak across organizations
6. Search returns results within 200ms for queries matching fewer than 1000 candidates
