# AgencyOS — AI-Native ATS for Staffing Agencies

A cloud-based, multi-tenant applicant tracking system built for external recruitment and staffing agencies serving the US, UK, and EU markets. AI functions exclusively as decision support — all candidate ranking and shortlist decisions require human approval. Classified as a **High-Risk AI System** under EU AI Act Annex III, Point 4(a).

## Portals & Interfaces

| Component | Stack | Default URL |
|-----------|-------|-------------|
| **Streamlit Portal** | Streamlit | `http://localhost:8501` |
| **Next.js Web Portal** | Next.js 14, Tailwind, React | `http://localhost:3000` |
| **FastAPI Backend** | FastAPI, Async SQLAlchemy 2.0, Postgres, Redis | `http://localhost:8001` (Docs: `/docs`) |
| **GitHub Pages Mockup** | HTML/JS | https://astraaaiagents.github.io/ats-ai/agent-portal.html |

---

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

## Technical Architecture & AI Multi-Agent System

- **Backend:** FastAPI (async) · SQLAlchemy 2.0+ (async) · PostgreSQL (pgvector + tsvector) · Redis · JWT (python-jose) · bcrypt
- **Multi-tenant Isolation:** Tenant scoping via `SET LOCAL app.organization_id` + PostgreSQL Row-Level Security (RLS) policies
- **Agent Orchestrator:** LangGraph state graph with discrete specialist nodes:
  - **IntentClassifier:** LLM-based intent recognition with instant 5s fallback to keyword matching
  - **SourcingAgent:** Hybrid search combining SQL filters, full-text search (`tsvector`), and vector similarity (`pgvector`) via Reciprocal Rank Fusion (RRF)
  - **RankingAgent:** Deterministic fit-score engine evaluating candidate skills, experience, and recruiter preferences
  - **OutreachAgent:** LLM-powered candidate email and message drafting
- **Real-Time Streaming:** Server-Sent Events (SSE) emitting `message_start`, `content`, `card`, `action`, and `message_end`

---

## Current API Surface

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/api/v1/health` | GET | Public | Health check |
| `/api/v1/auth/*` | — | Mixed | Login, register, refresh, password reset |
| `/api/v1/agent/conversation` | POST | Authenticated | Send message, stream response via SSE |
| `/api/v1/agent/sessions` | GET/DELETE | Authenticated | List or delete recruiter conversation sessions |
| `/api/v1/agent/preferences` | GET/PUT | Authenticated | Read or update explicit recruiter preferences |
| `/api/v1/agent/proactive/alerts` | GET | Authenticated | Fetch proactive AI notifications and candidate alerts |
| `/api/v1/agent/action-log` | GET | Authenticated | EU AI Act audit trail log |
| `/api/v1/candidates/*` | — | Authenticated | CRUD, skills, timeline, status transitions, duplicates |
| `/api/v1/organizations` | POST/GET/PUT | SuperAdmin | Multi-tenant organization administration |
| `/api/v1/users` | GET/POST/PUT/DELETE | Admin/Manager | List, invite, update, or deactivate users |
| `/api/v1/client-contacts` | GET/POST/PUT/DELETE | Admin/Manager | Client contact management |

---

## How to Run Locally

### Prerequisites

- Python 3.11+
- Node.js 18+ and `npm`
- PostgreSQL (with `pgvector` extension) & Redis (or run via Docker Compose)

---

### Option 1: Manual Local Setup

#### 1. Configure Environment Variables
Copy `.env.example` to `.env` in the root and `backend/` directories:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Key environment settings in `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ats_ai
REDIS_URL=redis://localhost:6379/0
DEV_MODE=true
BYPASS_AUTH=true
OPENAI_API_KEY=1234
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_MODEL=Qwen3.5-4B-MLX-4bit
```

#### 2. Setup & Start Backend (FastAPI)
```bash
cd backend

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations & initial setup
alembic -c db/alembic.ini upgrade head
python -m scripts.bootstrap
python -m scripts.setup_rls

# Start backend server on port 8001
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 3. Start Streamlit Recruiter Portal
In a new terminal window:
```bash
# From repo root with active virtualenv
source backend/.venv/bin/activate
streamlit run streamlit_app/app.py
```
Open `http://localhost:8501` in your browser.

#### 4. Start Next.js Frontend (Optional)
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

### Option 2: Docker Compose (Full Stack)

From repo root:
```bash
docker compose up --build
```
This starts PostgreSQL, Redis, and the FastAPI API backend containerized.

---

## Running Tests

### Backend Unit & Integration Tests
**241+ tests passing** — runs fully mock-isolated (no external service or LLM required):
```bash
cd backend
.venv/bin/pytest
```

To run a specific test file:
```bash
cd backend
.venv/bin/pytest tests/test_agent_routes.py -v
```

### End-to-End Playwright Tests
Run real browser E2E tests against Next.js / Streamlit portals:
```bash
cd frontend
npx playwright test
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
