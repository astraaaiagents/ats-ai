# Customer Showcase Deployment Guide

This guide details the step-by-step procedure to deploy the ATS AI application for customer demonstrations and showcases.

---

## 1. Environment Overview & Prerequisites

### Architecture Components
- **Frontend**: Next.js 16 (App Router) + React Query + Tailwind CSS
- **Backend**: FastAPI Async Application (Python 3.14)
- **Database**: PostgreSQL with Row-Level Security (RLS) enabled
- **Cache & Rate Limiting**: Redis
- **Containerization**: Docker & Docker Compose

### Prerequisites
- Docker & Docker Compose installed
- Domain / Subdomain with SSL/TLS certificate configured (or local reverse proxy / ngrok for staging)
- OpenAI API Key (`OPENAI_API_KEY`) for live agent responses

---

## 2. Step-by-Step Deployment Procedure

### Step 1: Environment Configuration
Copy `.env.example` to `.env` in the root repository and configure the production variables:

```bash
cp .env.example .env
```

Set the following required keys in `.env`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<secure-db-password>
POSTGRES_DB=ats_ai
DATABASE_URL=postgresql+asyncpg://postgres:<secure-db-password>@postgres:5432/ats_ai

REDIS_URL=redis://redis:6379/0

SECRET_KEY=<generate-long-random-jwt-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

OPENAI_API_KEY=sk-...

NEXT_PUBLIC_API_URL=https://<your-domain>/api/v1
```

---

### Step 2: Spin Up Infrastructure Containers
Run Docker Compose to start PostgreSQL, Redis, Backend API, and Next.js Frontend:

```bash
docker compose up -d --build
```

Verify that all services are running and healthy:
```bash
docker compose ps
```

---

### Step 3: Run Database Migrations & Multi-Tenant Setup
Execute database migrations and initialize RLS policies:

```bash
# 1. Run Alembic database migrations
docker compose exec api alembic -c db/alembic.ini upgrade head

# 2. Enable PostgreSQL Row-Level Security (RLS) policies
docker compose exec api python -m scripts.setup_rls

# 3. Bootstrap initial Superadmin user & Default Organization
docker compose exec api python -m scripts.bootstrap
```

---

### Step 4: Verification & Showcase Health Check

1. **Verify Backend Health**:
   ```bash
   curl -I https://<your-domain>/health
   ```
   Should return `HTTP/1.1 200 OK`.

2. **Verify Frontend Access**:
   Navigate to `https://<your-domain>/login` in your web browser.
   - Test login with superadmin credentials or Dev Quick Login.
   - Check Feed view, Candidate Pipeline, Job Postings, and Command Center.

---

## 3. Demo Data Pre-Seeding (Optional for Showcase)

To pre-populate demo jobs and candidate profiles before the showcase:
1. Navigate to the **Jobs** tab and click **+ New Job** to add target open roles.
2. Navigate to the **Pipeline** tab and click **+ New Candidate** to populate initial candidates.
3. Test candidate status transitions directly on Kanban cards.
