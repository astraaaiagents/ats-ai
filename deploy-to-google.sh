#!/usr/bin/env bash
# ==============================================================================
# Deploy ATS AI to Google Cloud (Cloud Build + Cloud Run)
# ==============================================================================
set -e

# Default Configuration
PROJECT_ID="${GCP_PROJECT_ID:-project-fd57960c-bd1d-4bf4-bf9}"
REGION="${GCP_REGION:-us-central1}"
ARTIFACT_REPO="${ARTIFACT_REPO:-ats-ai}"
BACKEND_SERVICE="${BACKEND_SERVICE_NAME:-ats-ai-backend}"
STREAMLIT_SERVICE="${STREAMLIT_SERVICE_NAME:-ats-ai-streamlit}"
OPENAI_KEY="${OPENAI_API_KEY:-}"

# Text Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}       ATS AI — Google Cloud Deployment Tool         ${NC}"
echo -e "${BLUE}=====================================================${NC}"
echo -e "Project ID:          ${GREEN}${PROJECT_ID}${NC}"
echo -e "Region:              ${GREEN}${REGION}${NC}"
echo -e "Artifact Repository: ${GREEN}${ARTIFACT_REPO}${NC}"
echo -e "Backend Service:     ${GREEN}${BACKEND_SERVICE}${NC}"
echo -e "Frontend Service:    ${GREEN}${STREAMLIT_SERVICE}${NC}"
echo -e "${BLUE}=====================================================${NC}\n"

# Step 1: Pre-flight Checks
echo -e "${YELLOW}[1/6] Running pre-flight CLI checks...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: 'gcloud' CLI is not installed. Please install Google Cloud SDK.${NC}"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)
if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo -e "${RED}Error: No active gcloud session found. Please run 'gcloud auth login'.${NC}"
    exit 1
fi

echo -e "Active GCP Account: ${GREEN}${ACTIVE_ACCOUNT}${NC}"
gcloud config set project "${PROJECT_ID}" --quiet

# Step 2: Enable Required GCP APIs
echo -e "\n${YELLOW}[2/6] Enabling required GCP APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Step 3: Ensure Artifact Registry Exists
echo -e "\n${YELLOW}[3/6] Verifying Artifact Registry repository...${NC}"
if ! gcloud artifacts repositories describe "${ARTIFACT_REPO}" --location="${REGION}" &>/dev/null; then
    echo -e "Creating Artifact Registry repository '${ARTIFACT_REPO}' in region '${REGION}'..."
    gcloud artifacts repositories create "${ARTIFACT_REPO}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="ATS AI Container Images" \
        --quiet
else
    echo -e "Artifact Registry repository '${ARTIFACT_REPO}' exists."
fi

# Step 4: Build and Deploy Backend Service
echo -e "\n${YELLOW}[4/6] Building & Deploying Backend Service ('${BACKEND_SERVICE}')...${NC}"
echo -e "Submitting Cloud Build job for backend..."
gcloud builds submit --config=backend_cloudbuild.yaml .

echo -e "Deploying backend container image to Cloud Run..."
DEPLOY_BACKEND_CMD="gcloud run deploy ${BACKEND_SERVICE} \
    --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/backend:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --port 8000"

if [ -n "$OPENAI_KEY" ]; then
    DEPLOY_BACKEND_CMD="${DEPLOY_BACKEND_CMD} --set-env-vars OPENAI_API_KEY=${OPENAI_KEY}"
fi

eval $DEPLOY_BACKEND_CMD

BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" --region="${REGION}" --format="value(status.address.url)")
echo -e "${GREEN}Backend successfully deployed at: ${BACKEND_URL}${NC}"

# Step 5: Build and Deploy Streamlit Frontend
echo -e "\n${YELLOW}[5/6] Building & Deploying Streamlit Frontend ('${STREAMLIT_SERVICE}')...${NC}"
echo -e "Submitting Cloud Build job for Streamlit frontend..."
gcloud builds submit --config=streamlit_cloudbuild.yaml .

echo -e "Deploying Streamlit container image to Cloud Run..."
gcloud run deploy "${STREAMLIT_SERVICE}" \
    --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/streamlit-app:latest" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 8501 \
    --set-env-vars "BACKEND_URL=${BACKEND_URL}"

STREAMLIT_URL=$(gcloud run services describe "${STREAMLIT_SERVICE}" --region="${REGION}" --format="value(status.address.url)")
echo -e "${GREEN}Streamlit Frontend successfully deployed at: ${STREAMLIT_URL}${NC}"

# Step 6: Post-Deployment Health Check
echo -e "\n${YELLOW}[6/6] Verifying deployment health...${NC}"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BACKEND_URL}/health" || echo "000")

if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo -e "${GREEN}Backend Health Check: PASSED (HTTP 200)${NC}"
else
    echo -e "${YELLOW}Backend Health Check: HTTP ${HEALTH_STATUS} (Service waking up or initializing)${NC}"
fi

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}         DEPLOYMENT COMPLETED SUCCESSFULLY!          ${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo -e "Backend API URL:    ${BLUE}${BACKEND_URL}${NC}"
echo -e "Streamlit App URL:  ${BLUE}${STREAMLIT_URL}${NC}"
echo -e "API Documentation:  ${BLUE}${BACKEND_URL}/docs${NC}"
echo -e "${GREEN}=====================================================${NC}\n"
