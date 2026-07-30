# Deploy ATS AI to Google Cloud Platform Guide

This document provides complete instructions and architectural details for deploying the **ATS AI** platform (FastAPI Backend + Streamlit Frontend) to **Google Cloud Platform (GCP)** using **Cloud Run** and **Artifact Registry**.

---

## 🚀 Quick Start (Automated Deployment)

We provide an automated, end-to-end deployment script (`deploy-to-google.sh`) that handles API enablement, container builds, image pushing, Cloud Run deployment, environment linking, and post-deploy health checks.

### Run Automated Deployment

```bash
# Optional: Set your OpenAI API Key before running
export OPENAI_API_KEY="sk-proj-..."

# Execute the deployment script
./deploy-to-google.sh
```

---

## 🏗️ Architecture Overview

The application is deployed across two serverless **Google Cloud Run** services:

```
                          ┌───────────────────────────┐
                          │   Google Cloud Run        │
                          │   (Streamlit Frontend)    │
                          │   ats-ai-streamlit        │
                          └─────────────┬─────────────┘
                                        │
                               HTTP / Stream JSON
                                        ▼
                          ┌───────────────────────────┐
                          │   Google Cloud Run        │
                          │   (FastAPI Backend)       │
                          │   ats-ai-backend          │
                          └─────────────┬─────────────┘
                                        │
                       ┌────────────────┴────────────────┐
                       │                                 │
                       ▼                                 ▼
         ┌───────────────────────────┐     ┌───────────────────────────┐
         │ PostgreSQL / SQLite DB     │     │ OpenAI API / LLM Services │
         │ (Auto-seeded candidates)  │     │ (Agent Sourcing & Fit)    │
         └───────────────────────────┘     └───────────────────────────┘
```

1. **Backend Service (`ats-ai-backend`)**:
   - **Framework**: FastAPI (Async Python 3.14 / 3.12)
   - **Port**: `8000`
   - **Database**: PostgreSQL / SQLite (`/tmp/ats_ai.db` in Cloud Run container)
   - **Auto-Initialization**: On service startup, `ensure_seed_candidates()` seeds 10 realistic candidate profiles automatically if absent.

2. **Frontend Service (`ats-ai-streamlit`)**:
   - **Framework**: Streamlit
   - **Port**: `8501`
   - **Communication**: Communicates asynchronously with `ats-ai-backend` via HTTP REST and SSE streams (`BACKEND_URL`).

---

## 📋 Prerequisites & Setup

Before running the deployment script or manual commands, ensure you have:

1. **Google Cloud SDK (`gcloud`)** installed and authenticated:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

2. **GCP Project & Billing** enabled:
   ```bash
   gcloud config set project project-fd57960c-bd1d-4bf4-bf9
   ```

3. **OpenAI API Key**:
   Required for real-time candidate fit score calculations and AI conversational responses.

---

## 🛠️ Step-by-Step Manual Deployment

If you prefer executing steps manually, follow these instructions:

### Step 1: Enable Required GCP APIs

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --region=us-central1
```

### Step 2: Create Artifact Registry Repository

Create a Docker repository named `ats-ai` in `us-central1`:

```bash
gcloud artifacts repositories create ats-ai \
    --repository-format=docker \
    --location=us-central1 \
    --description="ATS AI Container Images"
```

### Step 3: Build & Deploy FastAPI Backend

1. **Submit Cloud Build Job**:
   ```bash
   gcloud builds submit --config=backend_cloudbuild.yaml .
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy ats-ai-backend \
       --image us-central1-docker.pkg.dev/project-fd57960c-bd1d-4bf4-bf9/ats-ai/backend:latest \
       --region us-central1 \
       --platform managed \
       --allow-unauthenticated \
       --port 8000 \
       --set-env-vars "OPENAI_API_KEY=your-key-here"
   ```

3. **Get Backend Service URL**:
   ```bash
   export BACKEND_URL=$(gcloud run services describe ats-ai-backend --region=us-central1 --format="value(status.address.url)")
   echo "Backend Live URL: $BACKEND_URL"
   ```

### Step 4: Build & Deploy Streamlit Frontend

1. **Submit Cloud Build Job**:
   ```bash
   gcloud builds submit --config=streamlit_cloudbuild.yaml .
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy ats-ai-streamlit \
       --image us-central1-docker.pkg.dev/project-fd57960c-bd1d-4bf4-bf9/ats-ai/streamlit-app:latest \
       --region us-central1 \
       --platform managed \
       --allow-unauthenticated \
       --port 8501 \
       --set-env-vars "BACKEND_URL=$BACKEND_URL"
   ```

3. **Get Streamlit App URL**:
   ```bash
   gcloud run services describe ats-ai-streamlit --region=us-central1 --format="value(status.address.url)"
   ```

---

## ⚙️ Environment Variables Reference

### Backend (`ats-ai-backend`)

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Key for OpenAI LLM agent calls | `sk-proj-...` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:////tmp/ats_ai.db` |
| `SECRET_KEY` | JWT signing secret | `super-secret-key-for-jwt` |
| `JWT_ALGORITHM` | Encryption algorithm | `HS256` |
| `PORT` | Service listening port | `8000` |

### Frontend (`ats-ai-streamlit`)

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `BACKEND_URL` | Target FastAPI backend URL | `https://ats-ai-backend-616500568880.us-central1.run.app` |
| `PORT` | Service listening port | `8501` |

---

## 🔍 Verification & Health Checks

1. **Backend Health Check**:
   ```bash
   curl -i https://ats-ai-backend-616500568880.us-central1.run.app/health
   # Expected Output: HTTP/1.1 200 OK
   ```

2. **Backend Swagger API Specs**:
   Navigate to `https://ats-ai-backend-616500568880.us-central1.run.app/docs`.

3. **Candidates API Test**:
   ```bash
   curl -H "Authorization: Bearer dev-token" \
     https://ats-ai-backend-616500568880.us-central1.run.app/api/v1/candidates
   ```

4. **Streamlit UI Test**:
   Open `https://ats-ai-streamlit-616500568880.us-central1.run.app/` in your browser.

---

## 🐛 Troubleshooting

- **500 Internal Server Error / Missing Table**:
  Ensure database migrations or startup `ensure_seed_candidates()` ran successfully. Check logs using:
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ats-ai-backend" --limit 50
  ```

- **0 Candidates Returned in Sourcing Agent**:
  Verify `TenantMiddleware` in `app/middleware/tenant.py` properly sets `request.state.organization_id = "00000000-0000-0000-0000-000000000001"` when `Authorization: Bearer dev-token` is passed.

- **Cloud Run Cold Start Latency**:
  To minimize cold starts for live demos, configure minimum instances:
  ```bash
  gcloud run services update ats-ai-backend --min-instances=1 --region=us-central1
  ```
