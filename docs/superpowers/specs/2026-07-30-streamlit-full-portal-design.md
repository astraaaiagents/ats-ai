# Streamlit Full ATS Portal Design Spec

**Date**: 2026-07-30  
**Status**: Approved  
**Target Module**: `streamlit_app/`

---

## 1. Executive Summary

This specification expands the `streamlit_app/` application from a chat-only view into a complete **Streamlit ATS Portal** that replaces all features of the Next.js portal. The Streamlit app will feature top-level navigation tabs for Conversations, Proactive Feeds, Candidate Pipeline, Job Openings, and Recruiter Preferences.

---

## 2. Directory Layout & Architecture

```
streamlit_app/
├── app.py                     # Main Streamlit application entry point with st.tabs
├── api_client.py              # API Client with methods for agent, candidates, alerts, preferences
├── requirements.txt           # Python dependencies
├── components/
│   ├── sidebar.py             # Global session sidebar & recruiter context
│   ├── chat_view.py           # AI Recruiter Chat & SSE streaming
│   ├── feed_view.py           # Proactive AI feeds & alert cards
│   ├── pipeline_view.py       # Candidate Kanban / Stage management view
│   ├── jobs_view.py           # Job openings view & candidate matching
│   ├── preferences_view.py    # Recruiter preference controls & weights
│   └── cards.py               # Shared UI card renderers (candidate, job, alert)
└── README.md                  # Quickstart guide
```

---

## 3. View Specifications

### 3.1 Tab 1: 💬 Conversations & Chat (`components/chat_view.py`)
- Real-time token streaming via SSE (`POST /api/v1/agent/conversation`).
- Inline candidate, job, and alert card rendering.

### 3.2 Tab 2: ⚡ Feeds & Alerts (`components/feed_view.py`)
- Fetches proactive notifications from `GET /api/v1/agent/proactive/alerts`.
- Grouped by severity (*High*, *Medium*, *Info*).
- Displays candidate updates, job match notifications, and recruiter action items.

### 3.3 Tab 3: 📊 Candidate Pipeline (`components/pipeline_view.py`)
- Fetches candidate list from `GET /api/v1/candidates?limit=100`.
- Renders columns or select filters for pipeline stages:
  - `Sourced` ➔ `In Review` ➔ `Submitted` ➔ `Interview` ➔ `Offer` ➔ `Hired` / `Rejected`
- Shows fit score, skills, contact info, and stage transition dropdown/buttons (`PUT /api/v1/candidates/{id}/status`).

### 3.4 Tab 4: 💼 Job Openings (`components/jobs_view.py`)
- Displays active job requisitions and requirements.
- Lists top matched candidates per job requisition with fit score metrics.

### 3.5 Tab 5: ⚙️ Preferences (`components/preferences_view.py`)
- Fetches recruiter preferences from `GET /api/v1/agent/preferences`.
- Provides controls for minimum experience, required skills, remote preference, and automation weights.
- Saves changes via `PUT /api/v1/agent/preferences`.

---

## 4. Verification Strategy

1. Run unit tests across all component renderers and API client methods in `streamlit_app/tests/`.
2. Launch `streamlit run streamlit_app/app.py` and verify tab switching across all 5 views.
