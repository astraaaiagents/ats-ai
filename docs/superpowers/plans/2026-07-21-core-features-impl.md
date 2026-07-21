# Core Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the 7 core feature sections (4.1.1–4.1.7) from the Core Features spec: multi-tenant platform, candidate management, job/requisition management, submission workflow, CRM/outreach, client portal, and search/reporting.

**Architecture:** Monolithic backend API (Python/FastAPI recommended) serving a single-page frontend application. PostgreSQL with Row-Level Security for tenant isolation, JWT auth, WebSocket for real-time pipeline updates. Background jobs for async operations (report exports). Cursor-based pagination on all list endpoints.

**Tech Stack (recommended):** Python 3.12+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 16, Redis (job queue, WebSocket pub/sub), JWT (python-jose), bcrypt, APScheduler or Celery for scheduled tasks, pytest + httpx for testing. Frontend: React 18+ with TypeScript or Vue 3.

## Global Constraints

- All list endpoints use cursor-based pagination; default limit 25, max 100
- All responses use the standard error envelope: `{ error: { code, message, details } }`
- All tenant-scoped tables include `organization_id UUID NOT NULL` with RLS policy
- RLS enforced via `SET LOCAL app.organization_id` from JWT `org_id` claim
- API prefix: `/api/v1/`
- Rate limits: per-tenant 1000 req/min, per-user 200 req/min, burst 50 req/s
- Soft-delete: status-based entities transition to terminal state; non-status entities use `is_active` boolean
- Every API response includes `X-Request-ID` header (UUID)
- Access token TTL: 24h; refresh token TTL: 30d; revocation via `token_version` on user record
- All entities must have `created_at` and `updated_at` timestamptz columns with `now()` default

---

## Phase 0: Project Scaffolding & Cross-Cutting Foundation

**Goal:** Set up the project skeleton, database connection, auth middleware, error handling, and core conventions that every feature depends on.

### Task 0.1: Initialize Project Structure

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`

**Interfaces:**
- Consumes: (none — this is the entry point)
- Produces: `app.main.create_app()` — FastAPI application factory, `app.config.settings` — pydantic Settings singleton

- [ ] Step 1: Create `pyproject.toml` with FastAPI, SQLAlchemy async, Alembic, pytest, httpx dependencies
- [ ] Step 2: Create `app/config.py` with pydantic BaseSettings for DATABASE_URL, REDIS_URL, JWT_SECRET, S3_BUCKET, etc.
- [ ] Step 3: Create `app/database.py` with async SQLAlchemy engine, session factory, and Base declarative model
- [ ] Step 4: Create `app/main.py` with FastAPI app factory, lifespan handler, CORS middleware
- [ ] Step 5: Create `docker-compose.yml` with PostgreSQL 16 + Redis services
- [ ] Step 6: Create `backend/Dockerfile` for the API service
- [ ] Step 7: Create `.env.example` with all required environment variables
- [ ] Step 8: Write test that app factory returns a working ASGI app

### Task 0.2: Error Handling & Pagination Middleware

**Files:**
- Create: `backend/app/middleware/__init__.py`
- Create: `backend/app/middleware/error_handler.py`
- Create: `backend/app/middleware/request_id.py`
- Create: `backend/app/middleware/pagination.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/common.py`

**Interfaces:**
- Consumes: `app.main.create_app()`
- Produces: `AppException(code, message, status_code, details)`, `ErrorResponse` pydantic model, `PaginationParams` dependency, `paginated_response()` helper

- [ ] Step 1: Define `AppException` class in `app/middleware/error_handler.py` with code, message, status_code, details fields
- [ ] Step 2: Define `ErrorResponse` pydantic model matching the spec's error envelope format
- [ ] Step 3: Register exception handlers on the app for `AppException`, `ValidationError`, `HTTPException`
- [ ] Step 4: Create `X-Request-ID` middleware that generates/forwards the correlation ID
- [ ] Step 5: Create `PaginationParams` FastAPI dependency (cursor, limit, sort) with validation
- [ ] Step 6: Create `paginated_response()` function that wraps data with pagination envelope
- [ ] Step 7: Create rate limiting dependency using Redis sliding window counter
- [ ] Step 8: Write tests for error envelope, pagination, rate limit behavior

### Task 0.3: Authentication & Multi-Tenancy Middleware

**Files:**
- Create: `backend/app/auth/__init__.py`
- Create: `backend/app/auth/jwt.py`
- Create: `backend/app/auth/password.py`
- Create: `backend/app/auth/dependencies.py`
- Create: `backend/app/middleware/tenant.py`

**Interfaces:**
- Consumes: `app.database.get_session()`, `app.config.settings`
- Produces: `create_access_token()`, `create_refresh_token()`, `verify_token()`, `hash_password()`, `verify_password()`, `get_current_user()` dependency, `get_org_id()` dependency

- [ ] Step 1: Implement `hash_password()` with bcrypt cost 12 in `app/auth/password.py`
- [ ] Step 2: Implement `create_access_token()` and `create_refresh_token()` with JWT (sub, org_id, role, token_version claims)
- [ ] Step 3: Implement `verify_token()` with expiry and token_version check
- [ ] Step 4: Create `get_current_user()` FastAPI dependency that extracts user from Bearer token
- [ ] Step 5: Create tenant middleware that sets `app.organization_id` from JWT org_id claim using `SET LOCAL`
- [ ] Step 6: Write tests for token creation, verification, expiry, and revocation

### Task 0.4: Database Setup & RLS

**Files:**
- Create: `backend/db/__init__.py`
- Create: `backend/db/alembic.ini`
- Create: `backend/db/versions/001_initial_schema.py`
- Create: `backend/scripts/setup_rls.py`

**Interfaces:**
- Consumes: `app.database.Base`
- Produces: Initial migration creates all base tables, RLS policies, required indexes

- [ ] Step 1: Initialize Alembic with async support
- [ ] Step 2: Create initial migration with all Cross-Cutting foundation elements (platform_users, organizations, users, client_contacts, audit_logs tables + indexes + unique constraints)
- [ ] Step 3: Create RLS policy migration — one policy per tenant-scoped table using the template policy
- [ ] Step 4: Create a setup script that bootstraps the first SuperAdmin user
- [ ] Step 5: Verify migration runs cleanly against a local PostgreSQL instance

---

## Phase 1: Multi-Tenant Platform (4.1.1)

**Dependencies:** Phase 0 complete (auth, RLS, database)
**Provides:** Organization CRUD, user management, invitation flow, password reset, client contacts

### Task 1.1: Organization & User Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/organization.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/platform_user.py`
- Create: `backend/app/models/client_contact.py`
- Create: `backend/app/models/audit_log.py`

**Interfaces:**
- Consumes: `app.database.Base`
- Produces: SQLAlchemy ORM models for organizations, users (with token_version), platform_users, client_contacts, audit_logs

- [ ] Step 1: Define `Organization` model with columns matching 4.1.1 spec table
- [ ] Step 2: Define `User` model with organization_id FK, token_version column, unique partial index on (organization_id, email) WHERE is_active
- [ ] Step 3: Define `PlatformUser` model for SuperAdmin (no organization_id)
- [ ] Step 4: Define `ClientContact` model with organization_id FK, unique constraint on (organization_id, email)
- [ ] Step 5: Define `AuditLog` model with organization_id, event_type, resource_type, resource_id, metadata JSONB
- [ ] Step 6: Create Alembic migration for all models
- [ ] Step 7: Write model tests

### Task 1.2: Auth API Endpoints

**Files:**
- Create: `backend/app/routes/__init__.py`
- Create: `backend/app/routes/auth.py`
- Create: `backend/app/schemas/auth.py`

**Interfaces:**
- Consumes: `app.auth.*`, `User` model, `AuditLog` model
- Produces: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/forgot-password`, `POST /api/v1/auth/reset-password`

- [ ] Step 1: Implement `POST /api/v1/auth/login` — validate email+password, issue access+refresh tokens, log to audit_logs
- [ ] Step 2: Implement `POST /api/v1/auth/refresh` — validate refresh token, rotate, issue new pair
- [ ] Step 3: Implement `POST /api/v1/auth/forgot-password` — generate reset token (1h TTL), send email (placeholder)
- [ ] Step 4: Implement `POST /api/v1/auth/reset-password` — validate reset token, update password, invalidate sessions
- [ ] Step 5: Write integration tests for login, refresh, forgot-password, reset-password flows

### Task 1.3: Organization & User Management Endpoints

**Files:**
- Create: `backend/app/routes/organizations.py`
- Create: `backend/app/routes/users.py`
- Create: `backend/app/routes/client_contacts.py`
- Create: `backend/app/schemas/organization.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/client_contact.py`

**Interfaces:**
- Consumes: `Organization`, `User`, `ClientContact`, `PlatformUser` models, auth dependencies
- Produces: CRUD endpoints for organizations (SuperAdmin), users (Admin), client_contacts (Admin)

- [ ] Step 1: Implement organization endpoints — POST (SuperAdmin), GET/:id, PUT/:id; include `kms_key_id` in Organization model with note: KMS key rotation triggers re-encryption of new objects only, existing objects retain prior key
- [ ] Step 2: Implement user management — GET (list with pagination), POST /invite (generate 48h magic link, send email), resend-invite (reuses existing magic link, max 2 resends per link), PUT/:id, DELETE/:id (deactivate; if user deactivated, set their candidates' `owner_id = null`; on ownership transfer via PUT, require `reason` field)
- [ ] Step 3: Implement client_contacts CRUD — GET, POST, PUT/:id, DELETE/:id
- [ ] Step 4: Add role-based access control middleware that checks user.role against required role
- [ ] Step 5: Write integration tests verifying tenant isolation (User A cannot see User B's data)
- [ ] Step 6: Write tests for invitation expiration, password reset expiry, token revocation on deactivation

---

## Phase 2: Candidate Management (4.1.2)

**Dependencies:** Phase 1 complete (orgs, users, client_contacts, auth)
**Provides:** Candidate CRUD, resume upload, duplicate detection, status machine, timeline, document storage

### Task 2.1: Candidate Models

**Files:**
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/models/candidate.py`
- Create: `backend/app/models/candidate_skill.py`
- Create: `backend/app/models/candidate_document.py`
- Create: `backend/app/models/candidate_timeline.py`

**Interfaces:**
- Consumes: `Organization`, `User` models
- Produces: Candidate, CandidateSkill, CandidateDocument, CandidateTimeline ORM models with full schema from spec 4.1.2

- [ ] Step 1: Define `Candidate` model — organization_id FK, first_name, last_name, email, phone, current_title, current_employer, location, salary_expectation_min, salary_expectation_max, visa_status, notice_period_days, source (enum: linkedin, dribbble, github, referral, agency_db, manual), status, owner_id (FK -> users.id, nullable), ai_summary, ai_summary_generated_at, is_ai_summary_edited, created_at, updated_at; unique email partial index, status enforced at app layer
- [ ] Step 2: Define `CandidateSkill` model — organization_id, candidate_id FK, skill_name, proficiency, years_experience; unique on (candidate_id, skill_name)
- [ ] Step 3: Define `CandidateDocument` model — organization_id, candidate_id FK, document_type, file_name, file_size_bytes, s3_key, uploaded_by
- [ ] Step 4: Define `CandidateTimeline` model — organization_id, candidate_id FK, event_type (with CHECK constraint listing all valid types), description, metadata JSONB
- [ ] Step 5: Create Alembic migration
- [ ] Step 6: Write model tests

### Task 2.2: Candidate Status State Machine

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/candidate_status.py`

**Interfaces:**
- Consumes: `Candidate` model
- Produces: `validate_transition(from_status, to_status, user_role) → bool, allowed_transitions[]`, `get_allowed_transitions(status, user_role) → list`

- [ ] Step 1: Define state machine rules as a dict: `TRANSITIONS = { 'sourced': ['in_review', 'rejected'], 'in_review': ['submitted', 'rejected'], ... }`
- [ ] Step 2: Implement `validate_transition()` that checks from_status → to_status is valid and user has required role
- [ ] Step 3: Implement `get_allowed_transitions()` for UI to render available target states
- [ ] Step 4: Write exhaustive tests for every valid and invalid transition
- [ ] Step 5: Write tests for role-based transition restrictions

### Task 2.3: Candidate API Endpoints

**Files:**
- Create: `backend/app/routes/candidates.py`
- Create: `backend/app/services/candidate.py`
- Create: `backend/app/services/document_storage.py`
- Create: `backend/app/services/dedup.py`
- Create: `backend/app/schemas/candidate.py`

**Interfaces:**
- Consumes: Candidate models, candidate_status state machine, `document_storage` for S3 uploads
- Produces: Full candidate CRUD, upload, status change, dedup check, timeline, document endpoints

- [ ] Step 1: Implement `POST /api/v1/candidates` — create candidate manually with validation
- [ ] Step 2: Implement `POST /api/v1/candidates/upload` — multipart upload, S3 storage, enqueue background parse job
- [ ] Step 3: Implement `GET /api/v1/candidates` — list with pagination, filters (status, source, owner_id, skill), search by name/title
- [ ] Step 4: Implement `PATCH /api/v1/candidates/:id/status` — validate against state machine, auto-generate timeline event
- [ ] Step 5: Implement `POST /api/v1/candidates/dedup-check` — email exact match + phone+name Jaro-Winkler > 0.9
- [ ] Step 6: Implement document management endpoints — GET, POST (S3 upload), DELETE
- [ ] Step 7: Implement timeline endpoints — GET (paginated)
- [ ] Step 8: Implement candidate CRUD — GET/:id (with skills, documents, timeline), PUT/:id, DELETE/:id (soft-delete → archived)
- [ ] Step 9: Write integration tests for all endpoints including status transition validation
- [ ] Step 10: Write document upload and S3 integration tests

---

## Phase 3: Job & Requisition Management (4.1.3)

**Dependencies:** Phase 2 complete (candidates, client_contacts)
**Provides:** Requisition CRUD, skills management, requisition stages, status transitions

### Task 3.1: Requisition Models

**Files:**
- Create: `backend/app/models/requisition.py`
- Create: `backend/app/models/requisition_skill.py`
- Create: `backend/app/models/requisition_stage.py`

**Interfaces:**
- Consumes: `Organization`, `ClientContact`, `User` models
- Produces: Requisition, RequisitionSkill, RequisitionStage ORM models

- [ ] Step 1: Define `Requisition` model — all columns from spec (client_contact_id FK, status with CHECK, currency default USD)
- [ ] Step 2: Define `RequisitionSkill` model — organization_id, requisition_id FK, skill_name, is_required, min_years
- [ ] Step 3: Define `RequisitionStage` model — organization_id, stage_name, stage_order, is_default
- [ ] Step 4: Create Alembic migration
- [ ] Step 5: Write model tests

### Task 3.2: Requisition API Endpoints

**Files:**
- Create: `backend/app/routes/requisitions.py`
- Create: `backend/app/services/requisition_status.py`
- Create: `backend/app/schemas/requisition.py`

**Interfaces:**
- Consumes: Requisition models, `validate_requisition_transition()`
- Produces: CRUD endpoints for requisitions, skills, stages; status transition validation

- [ ] Step 1: Implement requisition CRUD — POST, GET (list with pagination, visibility rules: Recruiters see only their own + assigned; Admin/Manager see all), GET/:id (with skills, client_name via JOIN on client_contacts, pipeline counts), PUT/:id
- [ ] Step 2: Implement `PATCH /api/v1/requisitions/:id/status` with transition validation:
  - `in_progress → submitted`: requires at least one submitted shortlist
  - `submitted → filled`: requires `candidate_id` in payload
  - `any → closed`: requires `reason` enum (`filled`, `cancelled`, `on_hold`)
  - All transitions validated against state machine
- [ ] Step 3: Implement skill management — POST/:id/skills, DELETE/:id/skills/:skillId
- [ ] Step 4: Implement stage management — stage CRUD at `/api/v1/requisition-stages` (top-level: GET, POST, PUT/:id, DELETE/:id blocked if in use by active requisitions); reorder at `/api/v1/requisitions/:id/reorder-stages`
- [ ] Step 5: Implement pipeline counts via JOIN on shortlist_candidates grouped by status
- [ ] Step 6: Write integration tests for status transitions (including shortlist check, candidate_id requirement, closing reason enum), skill CRUD, stage CRUD

---

## Phase 4: Submission & Workflow Management (4.1.4)

**Dependencies:** Phase 2 + Phase 3 complete (candidates, requisitions)
**Provides:** Shortlists, shortlist candidates, interviews, placements, pipeline view, recycle pool

### Task 4.1: Shortlist & Placement Models

**Files:**
- Create: `backend/app/models/shortlist.py`
- Create: `backend/app/models/shortlist_candidate.py`
- Create: `backend/app/models/interview.py`
- Create: `backend/app/models/placement.py`

**Interfaces:**
- Consumes: `Requisition`, `Candidate`, `User` models
- Produces: Shortlist, ShortlistCandidate, Interview, Placement ORM models

- [ ] Step 1: Define `Shortlist` model — organization_id, requisition_id FK, name, status with CHECK, submitted_by, approved_by
- [ ] Step 2: Define `ShortlistCandidate` model — organization_id, shortlist_id FK, candidate_id FK, ai_rank, recruiter_rank, override_reason, status
- [ ] Step 3: Define `Interview` model — organization_id, shortlist_candidate_id FK, stage, scheduled_at, feedback, outcome
- [ ] Step 4: Define `Placement` model — organization_id FK, shortlist_candidate_id FK (UNIQUE), start_date, salary, fee_percentage, fee_amount (computed), guarantee_until, status
- [ ] Step 5: Implement fee computation in application layer: `fee_amount = salary * fee_percentage / 100`, recalculated on salary/fee_percentage change
- [ ] Step 6: Create Alembic migration
- [ ] Step 7: Write model tests

### Task 4.2: Shortlist & Workflow Endpoints

**Files:**
- Create: `backend/app/routes/shortlists.py`
- Create: `backend/app/services/shortlist.py`
- Create: `backend/app/schemas/shortlist.py`

**Interfaces:**
- Consumes: Shortlist models, candidate status service
- Produces: Shortlist CRUD, candidate management, approval gate, submission, placement creation, pipeline query, recycle pool

- [ ] Step 1: Implement shortlist CRUD — POST/:id/shortlists (with validation: max 25 candidates per shortlist), GET/:id/shortlists, POST/:id/shortlists/candidates, DELETE/:id/shortlists/candidates/:cid
- [ ] Step 2: Implement `POST /api/v1/shortlists/:id/approve` — verify all overrides logged, freeze ranking, change status
- [ ] Step 3: Implement `POST /api/v1/shortlists/:id/submit` — trigger portal link generation
- [ ] Step 4: Implement `PUT /api/v1/shortlist-candidates/:id/rank` — require override_reason if rank ≠ ai_rank
- [ ] Step 5: Implement interview logging — POST/:id/shortlist-candidates/:cid/interviews
- [ ] Step 6: Implement placement creation — POST/:id/shortlist-candidates/:cid/placement (auto-compute fee_amount)
- [ ] Step 7: Implement pipeline query — GET/:id/pipeline (aggregate counts by stage)
- [ ] Step 8: Implement recycle pool — GET /api/v1/recycle (rejected shortlist candidates)
- [ ] Step 9: Implement post-approval modification check — adding candidate to approved shortlist reverts to draft
- [ ] Step 10: Write integration tests for the full shortlist lifecycle (draft → approve → submit, override enforcement)

---

## Phase 5: Recruiter CRM & Outreach (4.1.5)

**Dependencies:** Phase 2 complete (candidates)
**Provides:** Sourcing lists, outreach templates, sequences, sequence steps, activities, activity feed

### Task 5.1: CRM Models

**Files:**
- Create: `backend/app/models/sourcing_list.py`
- Create: `backend/app/models/outreach_template.py`
- Create: `backend/app/models/outreach_sequence.py`
- Create: `backend/app/models/sequence_step.py`
- Create: `backend/app/models/activity.py`

**Interfaces:**
- Consumes: `Candidate`, `ClientContact`, `User` models
- Produces: SourcingList, SourcingListCandidate, OutreachTemplate, OutreachSequence, SequenceStep, Activity ORM models

- [ ] Step 1: Define `SourcingList` model — organization_id, name, description, created_by, created_at, updated_at
- [ ] Step 2: Define `SourcingListCandidate` model — organization_id, sourcing_list_id FK, candidate_id FK, notes, added_at
- [ ] Step 3: Define `OutreachTemplate` model — organization_id, name, subject, body, channel, variables JSONB, created_at, updated_at
- [ ] Step 4: Define `OutreachSequence` model — organization_id, name, is_active, created_at, updated_at
- [ ] Step 5: Define `SequenceStep` model — organization_id, sequence_id FK, template_id FK, step_order (unique per sequence), delay_hours, channel
- [ ] Step 6: Define `Activity` model — organization_id, candidate_id FK (nullable), client_contact_id FK (nullable), activity_type, description, metadata JSONB, performed_by, performed_at
- [ ] Step 7: Create Alembic migration
- [ ] Step 8: Write model tests

### Task 5.2: CRM API Endpoints

**Files:**
- Create: `backend/app/routes/sourcing_lists.py`
- Create: `backend/app/routes/outreach.py`
- Create: `backend/app/routes/activities.py`
- Create: `backend/app/schemas/crm.py`

**Interfaces:**
- Consumes: CRM models, candidate_timeline model
- Produces: CRUD for sourcing lists, templates, sequences, steps; outreach send, activity feed

- [ ] Step 1: Implement sourcing list CRUD — GET, POST, PUT/:id, DELETE/:id, POST/:id/candidates, DELETE/:id/candidates/:cid
- [ ] Step 2: Implement template CRUD at `/api/v1/outreach-templates` — GET, POST, PUT/:id, DELETE/:id
- [ ] Step 3: Implement sequence CRUD at `/api/v1/outreach-sequences` — GET, POST, PUT/:id, DELETE/:id
- [ ] Step 4: Implement step management — POST/:id/steps, PUT/:id/steps/:stepId, DELETE/:id/steps/:stepId, POST/:id/reorder-steps
- [ ] Step 5: Implement `POST /api/v1/outreach/send` — create Activity, mirror to candidate_timeline, check opt-out, enforce rate limit (max 3 outbound messages per candidate per day)
- [ ] Step 6: Implement `GET /api/v1/candidates/:id/activities` — paginated activity feed
- [ ] Step 7: Write integration tests for opt-out blocking, activity mirroring, template/sequence CRUD
- [ ] Step 8: Write tests for 409 on template delete when referenced by sequence_step

---

## Phase 6: Client Portal (4.1.6)

**Dependencies:** Phase 4 complete (shortlists, submissions), Phase 1 (client_contacts)
**Provides:** Magic link generation, OTP verification, client feedback, portal access log, WebSocket push

### Task 6.1: Portal Models & Magic Link Logic

**Files:**
- Create: `backend/app/models/client_portal.py`
- Create: `backend/app/services/portal.py`
- Create: `backend/app/schemas/portal.py`

**Interfaces:**
- Consumes: `ClientContact`, `ShortlistCandidate`, `Requisition` models
- Produces: ClientPortalSession, ClientFeedback, PortalAccessLog models; magic link generation + OTP logic

- [ ] Step 1: Define `ClientPortalSession` model — organization_id, client_contact_id FK, created_by FK (the recruiter), email (denormalized), client_name (denormalized), requisition_id FK, token (UNIQUE), otp_code, otp_expires_at, last_accessed_at, expires_at (7d), invalidated_at
- [ ] Step 2: Define `ClientFeedback` model — organization_id, shortlist_candidate_id FK, client_portal_session_id FK, decision, comment
- [ ] Step 3: Define `PortalAccessLog` model — client_portal_session_id FK, action, candidate_id FK (nullable), ip_address, user_agent
- [ ] Step 4: Implement magic link generation — create session with 7d TTL, generate unique token + 6-digit OTP (10min TTL), send email (placeholder)
- [ ] Step 5: Implement OTP verification — validate token + OTP, check expiration, track failed attempts (max 5)
- [ ] Step 6: Implement OTP resend endpoint (`POST /api/v1/client-portal/resend-otp`) with max 3 resends per magic link
- [ ] Step 7: Create Alembic migration
- [ ] Step 8: Write tests for OTP expiry, max failed attempts, resend limit, link invalidation

### Task 6.2: Portal API & WebSocket

**Files:**
- Create: `backend/app/routes/client_portal.py`
- Create: `backend/app/services/websocket_manager.py`

**Interfaces:**
- Consumes: Portal models, `Candidate` model (AI summary)
- Produces: Public portal endpoints (verify, verify-otp, submissions, feedback), WebSocket channel for pipeline updates

- [ ] Step 1: Implement `POST /api/v1/client-portal/generate-link` — recruiter triggers magic link generation (consumes magic link logic from Task 6.1 Step 4), accepts `client_contact_id`, `requisition_id`
- [ ] Step 2: Implement `GET /api/v1/client-portal/verify?token=` — show OTP verification screen
- [ ] Step 3: Implement `POST /api/v1/client-portal/verify-otp` — issue session cookie
- [ ] Step 4: Implement `GET /api/v1/client-portal/submissions` — list submitted candidates for this session (read-only); include `GET /api/v1/client-portal/submissions/:id` detail view
- [ ] Step 5: Implement `POST /api/v1/client-portal/feedback` — submit feedback, push to recruiter via WebSocket
- [ ] Step 6: Implement `POST /api/v1/client-portal/revoke/:sessionId` — admin endpoint to invalidate sessions
- [ ] Step 7: Implement `GET /api/v1/client-portal/access-log` — recruiter-facing access log
- [ ] Step 8: Build WebSocket manager — `ws://host/ws/pipeline/{requisition_id}` subscription with exponential backoff reconnection (1s, 2s, 4s)
- [ ] Step 9: Implement WebSocket event emission on feedback submission
- [ ] Step 10: Write integration tests for the full portal flow (generate → verify → OTP → submissions → feedback → WebSocket event)

---

## Phase 7: Search & Reporting (4.1.7)

**Dependencies:** All previous phases complete (all entities exist in database)
**Provides:** Full-text search, faceted filters, pipeline dashboard, submission metrics, recruiter productivity, report exports

### Task 7.1: Search & Dashboard

**Files:**
- Create: `backend/app/models/search.py`
- Create: `backend/app/routes/search.py`
- Create: `backend/app/routes/dashboards.py`
- Create: `backend/app/services/search.py`
- Create: `backend/app/schemas/search.py`

**Interfaces:**
- Consumes: All entity models (candidates, requisitions, etc.)
- Produces: Full-text search endpoints (candidates + requisitions), dashboard endpoints (pipeline, submissions, recruiter)

- [ ] Step 1: Define `SearchLog` model — organization_id, user_id, query, filters JSONB, result_count
- [ ] Step 2: Define `ReportDefinition` model — organization_id, name, type, config JSONB, created_by
- [ ] Step 3: Add GIN index migration for tsvector on candidates(name, title, skills) and requisitions(title, description)
- [ ] Step 4: Implement `GET /api/v1/search/candidates` — ts_query with GIN search, filters AND-combined, ranking (ts_rank * recency_boost * owner_boost where recency_boost=1.2 for updated in last 7d else 1.0, owner_boost=1.1 for owned by searching user else 1.0), cursor pagination; 414 if URL > 4K chars; implement `POST /api/v1/search/candidates` as JSON body fallback for long queries
- [ ] Step 5: Implement `GET /api/v1/search/requisitions` — same pattern for requisitions; implement `POST /api/v1/search/requisitions` as JSON body fallback
- [ ] Step 6: Implement pipeline dashboard — query materialized view `mv_pipeline_counts`
- [ ] Step 7: Implement submission metrics dashboard — query `mv_submission_metrics`
- [ ] Step 8: Implement recruiter productivity dashboard — query `mv_recruiter_productivity`
- [ ] Step 9: Create materialized view migration scripts for all 3 views with refresh function
- [ ] Step 10: Implement scheduled refresh (cron job via APScheduler or pg_cron) every 15 minutes; on refresh failure, retain previous data and send admin alert
- [ ] Step 11: Write search ranking tests verifying ts_rank * boost multipliers

### Task 7.2: Report Export

**Files:**
- Create: `backend/app/routes/reports.py`
- Create: `backend/app/services/report_export.py`

**Interfaces:**
- Consumes: `SearchLog`, dashboard data, WebSocket manager
- Produces: Async report export with WebSocket notification on completion

- [ ] Step 1: Implement `POST /api/v1/reports/:type/export` — enqueue async export job, return export_id
- [ ] Step 2: Implement background export worker — generate CSV/PDF with streaming for >1000 rows
- [ ] Step 3: Implement `GET /api/v1/reports/exports/:exportId` — download completed export
- [ ] Step 4: Emit WebSocket `report_ready` event on completion (channel: `ws://host/ws/notifications/{user_id}`)
- [ ] Step 5: Write integration test for async export flow
