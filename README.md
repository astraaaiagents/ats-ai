# AgencyOS — AI-Native ATS for Staffing Agencies

A cloud-based, multi-tenant applicant tracking system built for external recruitment and staffing agencies serving the US, UK, and EU markets. AI functions exclusively as decision support — all candidate ranking and shortlist decisions require human approval. Classified as a **High-Risk AI System** under EU AI Act Annex III, Point 4(a).

## UI Mockup (GitHub Pages)

| Mockup | Link |
|--------|------|
| Agent-First Recruiter Portal | https://astraaaiagents.github.io/ats-ai/agent-portal.html |

## Product Overview

**Vision:** The operating system for modern staffing agencies — one platform where recruiters source, manage, engage, and submit candidates at scale with AI assistance, while keeping humans in control of hiring decisions.

**Core Value Propositions:**
- **Recruiter Efficiency:** Reduce candidate prep from ~45 min to under 5 min per submission
- **Speed to Submittal:** 50% faster first-submittal via semantic matching and AI summarization
- **Candidate Transparency:** AI-generated profile summaries, job recommendations, and clear AI disclosure
- **Turnkey Compliance:** EU AI Act high-risk compliance controls out of the box

### Personas

| Persona | Role |
|---------|------|
| **Account Manager** | Business development, clients, jobs — reviews shortlists, presents to clients |
| **Sourcer** | Finds and engages candidates — daily driver of CRM, AI parsers, outreach |
| **Candidate** | Self-service portal, AI summaries, job recommendations, consent management |
| **Client** | Read-only portal via magic link — reviews submissions, provides feedback |
| **Agency Admin** | Multi-tenant config, RBAC, compliance logs, LLM token cost control |

### Target Markets

USA, UK, EU — with GDPR/UK GDPR/CCPA alignment and EU AI Act compliance built in.

---

## Backend Implementation

**Stack:** FastAPI (async) · SQLAlchemy 2.0+ (async) · PostgreSQL · Redis · JWT (python-jose) · bcrypt

### Architecture

- **Multi-tenant:** Tenant isolation via `SET LOCAL app.organization_id` + PostgreSQL RLS
- **Auth:** JWT access + refresh tokens, Bearer `HTTPBearer`, token versioning for revocation
- **Pagination:** Cursor-based (default 25, max 100)
- **Error handling:** `AppException(code, message, status_code)` → `{"error": {...}}`
- **Migrations:** Raw Alembic Python files in `backend/db/versions/`

### Current API Surface

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/health` | GET | Public | Health check |
| `/api/v1/auth/*` | — | Mixed | Login, register, refresh, password reset |
| `/api/v1/candidates/*` | — | Authenticated | CRUD, skills, timeline, status, duplicates |
| `/api/v1/organizations` | POST | SuperAdmin | Create organization |
| `/api/v1/organizations/:id` | GET/PUT | SuperAdmin | Read/update organization |
| `/api/v1/users` | GET | Admin/Manager | List users (cursor pagination) |
| `/api/v1/users/invite` | POST | Admin/Manager | Invite via 48h magic link |
| `/api/v1/users/:id` | PUT/DELETE | Admin/Manager | Update/deactivate user |
| `/api/v1/client-contacts` | GET/POST | Admin/Manager | List/create client contacts |
| `/api/v1/client-contacts/:id` | PUT/DELETE | Admin/Manager | Update/soft-delete |

### Test Suite

**68 tests passing** — integration tests using `httpx.ASGITransport` (no real server), Redis mocked via `mock_redis` fixture. Coverage includes CRUD, role enforcement, auth enforcement, duplicate validation, tenant isolation, token revocation.

### Running Locally

```bash
# From the backend/ directory
cp .env.example .env          # edit DATABASE_URL, JWT_SECRET, REDIS_URL
pytest                        # run tests (no external services needed)
uvicorn app.main:app          # dev server
```

Or from repo root with full stack:
```bash
docker compose up
```

---

## Development Phases

| Phase | Focus | Timeline |
|-------|-------|----------|
| **1** | Core platform: multi-tenant, auth, candidate/job management, submission workflows | Months 1–3 |
| **2** | CRM & AI: resume parsing, AI summaries, sourcing, outreach, activity tracking | Months 3–4 |
| **3** | AI matching, ranking, client portal with magic-link auth | Months 4–5 |
| **4** | Compliance hardening, EU AI Act, bias monitoring, GA readiness | Months 5–6 |

Full PRD: [`deepseek-ats-ai.md`](./deepseek-ats-ai.md)

---

## Key Compliance Principles

- **Human approval required** for any AI-supported ranking or shortlist export
- **No automated rejection** — AI cannot reject or auto-select candidates
- **Override reasons captured** when recruiter changes an AI ranking
- **PII redacted** before any external LLM request via privacy shield middleware
- **Zero Data Retention** agreements with all LLM providers
- **Audit logging** for all AI interactions, prompts, outputs, and overrides
