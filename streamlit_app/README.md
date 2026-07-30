# ATS AI Streamlit Conversations & Chat App

Standalone Streamlit application for the AI Recruiter Gateway.

## Quickstart

1. Ensure the FastAPI backend is running at `http://localhost:8000`.
2. Install dependencies:
   ```bash
   pip install -r streamlit_app/requirements.txt
   ```
3. Launch Streamlit app:
   ```bash
   streamlit run streamlit_app/app.py
   ```
4. Access the web interface at `http://localhost:8501`.

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000/api/v1` | FastAPI base URL |
| `STREAMLIT_API_TOKEN` | `dev-token` | Bearer token for API auth |

## Components

- **Sidebar** — New conversation, starter prompts, recent session history
- **Chat View** — Message feed with SSE streaming and structured card rendering
- **Cards** — Candidate, job, and alert card components
