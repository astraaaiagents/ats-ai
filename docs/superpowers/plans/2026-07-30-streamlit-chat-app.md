# Streamlit Conversations & Chat Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace custom React chat UI with a native Python Streamlit application (`streamlit_app/app.py`) that connects to the FastAPI backend API via SSE streaming, offering chat messaging, sidebar session history, starter prompts, and structured cards.

**Architecture:** A standalone Streamlit app in `streamlit_app/` using `httpx` to consume Server-Sent Events (SSE) from FastAPI (`http://localhost:8000/api/v1/agent/conversation`). Uses `st.chat_message`, `st.chat_input`, and `st.sidebar` to manage user interactions and state in `st.session_state`.

**Tech Stack:** Streamlit 1.30+, Python 3.10+, `httpx`, `sseclient-py`.

## Global Constraints

- Backend API Base URL: `http://localhost:8000/api/v1`
- Auth Header: `Authorization: Bearer dev-token`
- Directory: All app files live under `streamlit_app/`
- Streamlit Port: 8501

---

### Task 1: Streamlit Environment Setup & Backend API Client

**Files:**
- Create: `streamlit_app/requirements.txt`
- Create: `streamlit_app/api_client.py`
- Test: `streamlit_app/tests/test_api_client.py`

**Interfaces:**
- Produces: `APIClient` class in `streamlit_app/api_client.py` with methods:
  - `get_action_log() -> list[dict]`
  - `get_conversation_history(session_id: str) -> list[dict]`
  - `stream_conversation(message: str, session_id: str | None) -> Generator[dict, None, None]`

- [ ] **Step 1: Write tests for `api_client.py`**

Create `streamlit_app/tests/test_api_client.py`:
```python
import pytest
from unittest.mock import MagicMock, patch
from streamlit_app.api_client import APIClient

def test_api_client_init():
    client = APIClient(base_url="http://localhost:8000/api/v1", token="dev-token")
    assert client.base_url == "http://localhost:8000/api/v1"
    assert client.headers["Authorization"] == "Bearer dev-token"

@patch("httpx.get")
def test_get_action_log(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": [{"id": "1", "action_type": "intent_parse"}]}
    mock_get.return_value = mock_resp

    client = APIClient()
    items = client.get_action_log()
    assert len(items) == 1
    assert items[0]["id"] == "1"
```

- [ ] **Step 2: Create `streamlit_app/requirements.txt`**

```text
streamlit>=1.30.0
httpx>=0.25.0
sseclient-py>=1.8.0
pytest>=8.0.0
```

- [ ] **Step 3: Implement `streamlit_app/api_client.py`**

```python
import os
import json
import logging
import httpx
from typing import Generator, Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class APIClient:
    """Client for FastAPI Agent Gateway endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")).rstrip("/")
        self.token = token or os.getenv("STREAMLIT_API_TOKEN", "dev-token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_action_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch past activity logs / sessions."""
        try:
            url = f"{self.base_url}/agent/action-log?limit={limit}"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching action log: {exc}")
            return []

    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch history for a specific session."""
        try:
            url = f"{self.base_url}/agent/conversation/{session_id}"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("messages", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching conversation {session_id}: {exc}")
            return []

    def stream_conversation(
        self,
        message: str,
        session_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Send message and yield parsed SSE events."""
        url = f"{self.base_url}/agent/conversation"
        payload = {"message": message, "session_id": session_id}

        try:
            with httpx.stream(
                "POST",
                url,
                json=payload,
                headers=self.headers,
                timeout=30.0,
            ) as response:
                current_event = "message"
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line.replace("event:", "").strip()
                    elif line.startswith("data:"):
                        raw_data = line.replace("data:", "").strip()
                        try:
                            data = json.loads(raw_data)
                            yield {"event": current_event, "data": data}
                        except json.JSONDecodeError:
                            yield {"event": current_event, "data": raw_data}
        except Exception as exc:
            logger.error(f"Error streaming conversation: {exc}")
            yield {"event": "error", "data": {"message": str(exc)}}
```

- [ ] **Step 4: Run tests**

Run: `pytest streamlit_app/tests/test_api_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit Task 1**

```bash
git add streamlit_app/
git commit -m "feat(streamlit): add API client and requirements"
```

---

### Task 2: Card & Sidebar UI Components

**Files:**
- Create: `streamlit_app/components/cards.py`
- Create: `streamlit_app/components/sidebar.py`

**Interfaces:**
- Consumes: `APIClient` from `streamlit_app/api_client.py`
- Produces:
  - `render_candidate_card(data: dict)`
  - `render_job_card(data: dict)`
  - `render_alert_card(data: dict)`
  - `render_sidebar(client: APIClient)`

- [ ] **Step 1: Create `streamlit_app/components/cards.py`**

```python
import streamlit as st
from typing import Dict, Any

def render_candidate_card(card: Dict[str, Any]):
    """Render structured candidate card."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**👤 {card.get('name', 'Candidate')}**")
            st.caption(f"Role: {card.get('title', 'N/A')} • Experience: {card.get('experience', 'N/A')}")
        with col2:
            score = card.get("fit_score", card.get("score"))
            if score is not None:
                st.metric(label="Fit Score", value=f"{int(float(score) * 100)}%")

        skills = card.get("skills", [])
        if skills:
            st.markdown(f"**Skills:** `{', '.join(skills[:6])}`")

        summary = card.get("summary")
        if summary:
            st.write(f"*{summary}*")

def render_job_card(card: Dict[str, Any]):
    """Render structured job card."""
    with st.container(border=True):
        st.markdown(f"**💼 {card.get('title', 'Job Opening')}**")
        st.caption(f"Company: {card.get('company', 'Internal')} • Location: {card.get('location', 'Remote')}")
        if card.get("description"):
            st.write(card["description"])

def render_alert_card(card: Dict[str, Any]):
    """Render proactive alert card."""
    severity = card.get("severity", "info").lower()
    icon = "⚠️" if severity == "warning" else "ℹ️"
    with st.container(border=True):
        st.markdown(f"**{icon} {card.get('title', 'Alert')}**")
        st.write(card.get("message", ""))
```

- [ ] **Step 2: Create `streamlit_app/components/sidebar.py`**

```python
import streamlit as st
from streamlit_app.api_client import APIClient

STARTER_PROMPTS = [
    {"title": "🎯 Source Candidates", "prompt": "Source top 5 Java engineers with AWS experience"},
    {"title": "📊 Pipeline Review", "prompt": "Review candidate fit scores for open positions"},
    {"title": "✉️ Draft Outreach", "prompt": "Draft personalized outreach emails for top candidates"},
]

def render_sidebar(client: APIClient):
    """Render sidebar with session history and new conversation trigger."""
    st.sidebar.title("🤖 AI Recruiter Agent")
    st.sidebar.caption("Recruiter Gateway Portal")

    if st.sidebar.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state["session_id"] = None
        st.session_state["messages"] = []
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Quick Starters")

    for starter in STARTER_PROMPTS:
        if st.sidebar.button(starter["title"], key=f"starter_{starter['title']}", use_container_width=True):
            st.session_state["session_id"] = None
            st.session_state["messages"] = []
            st.session_state["pending_prompt"] = starter["prompt"]
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Recent Conversations")

    logs = client.get_action_log(limit=20)
    seen_sessions = set()
    sessions = []

    for log in logs:
        sid = log.get("session_id")
        if sid and sid not in seen_sessions:
            seen_sessions.add(sid)
            sessions.append({
                "id": sid,
                "label": f"Session {sid[:8]}...",
                "time": log.get("created_at", "")[:10],
            })

    if not sessions:
        st.sidebar.info("No active conversation history")

    for s in sessions:
        is_active = st.session_state.get("session_id") == s["id"]
        btn_label = f"💬 {s['label']}" if not is_active else f"👉 {s['label']}"
        if st.sidebar.button(btn_label, key=f"session_{s['id']}", use_container_width=True):
            st.session_state["session_id"] = s["id"]
            history = client.get_conversation_history(s["id"])
            st.session_state["messages"] = [
                {
                    "role": msg.get("role", "assistant"),
                    "content": msg.get("content", ""),
                    "cards": msg.get("cards", []),
                }
                for msg in history
            ]
            st.rerun()
```

- [ ] **Step 3: Commit Task 2**

```bash
git add streamlit_app/components/
git commit -m "feat(streamlit): add cards and sidebar components"
```

---

### Task 3: Main Chat View, Entry Point & Quickstart Documentation

**Files:**
- Create: `streamlit_app/components/chat_view.py`
- Create: `streamlit_app/app.py`
- Create: `streamlit_app/README.md`

**Interfaces:**
- Consumes: `APIClient` and components from Task 1 & 2
- Produces: Complete running Streamlit application

- [ ] **Step 1: Create `streamlit_app/components/chat_view.py`**

```python
import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.cards import (
    render_candidate_card,
    render_job_card,
    render_alert_card,
)

def render_chat_view(client: APIClient):
    """Render main chat messages and handle prompt submission."""
    st.title("Conversations & Chat")
    st.caption("Interact with your AI Recruiter Agent for candidate sourcing, pipeline management, and outreach.")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display message history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            for card in msg.get("cards", []):
                ctype = card.get("type", "").lower()
                if "candidate" in ctype:
                    render_candidate_card(card)
                elif "job" in ctype:
                    render_job_card(card)
                elif "alert" in ctype:
                    render_alert_card(card)

    # Check for pending starter prompt
    pending_prompt = st.session_state.pop("pending_prompt", None)
    prompt = st.chat_input("Ask AI Recruiter...") or pending_prompt

    if prompt:
        # Save and display user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Stream assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            received_cards = []

            session_id = st.session_state.get("session_id")

            for event in client.stream_conversation(prompt, session_id=session_id):
                ev_type = event.get("event")
                data = event.get("data", {})

                if ev_type == "message_start" and isinstance(data, dict):
                    st.session_state["session_id"] = data.get("session_id")
                elif ev_type == "content":
                    content_chunk = data.get("content", "") if isinstance(data, dict) else str(data)
                    full_response += content_chunk
                    message_placeholder.markdown(full_response + "▌")
                elif ev_type == "card" and isinstance(data, dict):
                    received_cards.append(data)
                    ctype = data.get("type", "").lower()
                    if "candidate" in ctype:
                        render_candidate_card(data)
                    elif "job" in ctype:
                        render_job_card(data)
                    elif "alert" in ctype:
                        render_alert_card(data)

            message_placeholder.markdown(full_response)

            st.session_state["messages"].append({
                "role": "assistant",
                "content": full_response,
                "cards": received_cards,
            })
```

- [ ] **Step 2: Create `streamlit_app/app.py`**

```python
import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.chat_view import render_chat_view

st.set_page_config(
    page_title="ATS AI - Recruiter Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    client = APIClient()
    render_sidebar(client)
    render_chat_view(client)

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create `streamlit_app/README.md`**

```markdown
# ATS AI Streamlit Conversations & Chat App

Standalone Streamlit frontend for the AI Recruiter Gateway.

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
```

- [ ] **Step 4: Commit Task 3**

```bash
git add streamlit_app/
git commit -m "feat(streamlit): complete main chat view and app entry point"
```
