# Streamlit Conversations & Chat Application Design Spec

**Date**: 2026-07-30  
**Status**: Approved  
**Target Module**: `streamlit_app/`

---

## 1. Executive Summary

This specification outlines replacing the custom React/Next.js conversations and chat tab with a standalone Python **Streamlit application** (`streamlit_app/app.py`). The Streamlit application will serve as a native agent interface using `st.chat_message`, `st.chat_input`, and `st.sidebar`, communicating directly with the FastAPI backend (`http://localhost:8000/api/v1`).

---

## 2. Architecture & Directory Layout

```
streamlit_app/
├── app.py                     # Main Streamlit application entry point
├── api_client.py              # Async/Sync HTTP & SSE client for FastAPI (/api/v1/agent)
├── requirements.txt           # Dependencies (streamlit, httpx, sseclient-py)
├── components/
│   ├── sidebar.py             # Session history sidebar & New Conversation trigger
│   ├── chat_view.py           # Chat feed rendering & st.chat_input handling
│   └── cards.py               # Custom UI card rendering for candidates, jobs, and alerts
└── README.md                  # Quickstart guide for running Streamlit
```

---

## 3. Component Details & Data Flow

### 3.1 Backend Integration (`api_client.py`)
- **Base URL**: Configurable via environment variable `BACKEND_URL` (default: `http://localhost:8000/api/v1`).
- **Auth**: Sends `Authorization: Bearer dev-token` (or configured JWT token) to satisfy `get_current_user` dependency.
- **Endpoints Utilized**:
  - `POST /agent/conversation` (SSE stream for live token response, cards, and actions)
  - `GET /agent/conversation/{session_id}` (Retrieve past message history)
  - `GET /agent/action-log` (List past sessions and activity)
  - `GET /agent/proactive/alerts` (List proactive alerts)

### 3.2 Sidebar & Session Management (`components/sidebar.py`)
- Displays title and "New Conversation" button at top of sidebar.
- Renders starter prompt buttons:
  - *"Source top Java engineers"*
  - *"Review pipeline fit scores"*
  - *"Draft candidate outreach"*
- Lists recent conversation sessions fetched from backend.
- Manages `st.session_state["session_id"]` to switch contexts.

### 3.3 Main Chat View (`components/chat_view.py`)
- Displays conversation history in chronological order using `st.chat_message("user")` and `st.chat_message("assistant")`.
- When a user submits a prompt via `st.chat_input("Ask AI Recruiter...")`:
  1. Displays user message immediately.
  2. Opens an SSE stream to `POST /agent/conversation`.
  3. Appends incoming `content` tokens in real-time to an `st.empty()` placeholder inside `st.chat_message("assistant")`.
  4. Parses `card` and `action` SSE events to render interactive cards using `components/cards.py`.

### 3.4 Structured Card Rendering (`components/cards.py`)
- **Candidate Cards**: Renders candidate name, fit score badge, current title, key skills, and status transition buttons.
- **Job Cards**: Displays position title, company name, location, and requirement summary.
- **Alert Cards**: Highlights proactive notifications with priority indicators.

---

## 4. Environment & Execution

- **Port**: Runs on `http://localhost:8501`.
- **Command**: `streamlit run streamlit_app/app.py`
- **Dependencies**:
  - `streamlit>=1.30.0`
  - `httpx>=0.25.0`
  - `sseclient-py>=1.8.0`

---

## 5. Verification Strategy

1. Verify `streamlit_app/app.py` launches cleanly with `streamlit run`.
2. Test session creation, prompt submission, and SSE response streaming against live FastAPI backend.
3. Confirm past conversation history loads correctly when selecting a session in `st.sidebar`.
