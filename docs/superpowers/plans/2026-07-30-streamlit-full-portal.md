# Streamlit Full ATS Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `streamlit_app/` into a complete ATS Portal with navigation tabs for Conversations, Proactive Feeds, Candidate Pipeline, Job Openings, and Recruiter Preferences.

**Architecture:** Extend `api_client.py` with candidate, alert, and preference API methods. Create dedicated Streamlit view components (`feed_view.py`, `pipeline_view.py`, `jobs_view.py`, `preferences_view.py`) and wire them into `streamlit_app/app.py` using `st.tabs()`.

**Tech Stack:** Streamlit 1.30+, Python 3.10+, `httpx`, `pytest`.

## Global Constraints

- Backend API Base URL: `http://localhost:8000/api/v1`
- Auth Header: `Authorization: Bearer dev-token`
- Directory: All app files live under `streamlit_app/`

---

### Task 1: API Client Extensions (`streamlit_app/api_client.py`)

**Files:**
- Modify: `streamlit_app/api_client.py`
- Modify: `streamlit_app/tests/test_api_client.py`

**Interfaces:**
- Produces methods on `APIClient`:
  - `get_candidates(limit: int = 100, status: Optional[str] = None) -> list[dict]`
  - `update_candidate_status(candidate_id: str, new_status: str) -> bool`
  - `get_proactive_alerts() -> list[dict]`
  - `get_preferences() -> dict`
  - `update_preferences(explicit: dict) -> dict`

- [ ] **Step 1: Add tests for API client extension methods in `streamlit_app/tests/test_api_client.py`**

```python
@patch("httpx.get")
def test_get_candidates(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": [{"id": "c1", "first_name": "Jane", "last_name": "Doe"}]}
    mock_get.return_value = mock_resp

    client = APIClient()
    candidates = client.get_candidates()
    assert len(candidates) == 1
    assert candidates[0]["first_name"] == "Jane"

@patch("httpx.get")
def test_get_proactive_alerts(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"alerts": [{"id": "a1", "title": "High Fit Score"}]}
    mock_get.return_value = mock_resp

    client = APIClient()
    alerts = client.get_proactive_alerts()
    assert len(alerts) == 1
```

- [ ] **Step 2: Add API methods to `streamlit_app/api_client.py`**

```python
    def get_candidates(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch list of candidates with optional status filter."""
        try:
            url = f"{self.base_url}/candidates?limit={limit}"
            if status:
                url += f"&status={status}"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching candidates: {exc}")
            return []

    def update_candidate_status(self, candidate_id: str, new_status: str) -> bool:
        """Update a candidate's pipeline status."""
        try:
            url = f"{self.base_url}/candidates/{candidate_id}/status"
            payload = {"status": new_status, "reason": "Updated via Streamlit Portal"}
            resp = httpx.patch(url, json=payload, headers=self.headers, timeout=10.0)
            return resp.status_code == 200
        except Exception as exc:
            logger.error(f"Error updating candidate {candidate_id} status: {exc}")
            return False

    def get_proactive_alerts(()) -> List[Dict[str, Any]]:
        """Fetch proactive AI alerts and feeds."""
        try:
            url = f"{self.base_url}/agent/proactive/alerts"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("alerts", [])
            return []
        except Exception as exc:
            logger.error(f"Error fetching proactive alerts: {exc}")
            return []

    def get_preferences(self) -> Dict[str, Any]:
        """Fetch recruiter preferences."""
        try:
            url = f"{self.base_url}/agent/preferences"
            resp = httpx.get(url, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as exc:
            logger.error(f"Error fetching preferences: {exc}")
            return {}

    def update_preferences(self, explicit: Dict[str, Any]) -> Dict[str, Any]:
        """Update explicit recruiter preferences."""
        try:
            url = f"{self.base_url}/agent/preferences"
            payload = {"explicit": explicit}
            resp = httpx.put(url, json=payload, headers=self.headers, timeout=10.0)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as exc:
            logger.error(f"Error updating preferences: {exc}")
            return {}
```

- [ ] **Step 3: Run pytest**

Run: `PYTHONPATH=. backend/.venv/bin/pytest streamlit_app/tests/test_api_client.py -v`

- [ ] **Step 4: Commit Task 1**

```bash
git add streamlit_app/
git commit -m "feat(streamlit): extend API client for candidates, alerts, and preferences"
```

---

### Task 2: Feeds & Alerts View (`streamlit_app/components/feed_view.py`)

**Files:**
- Create: `streamlit_app/components/feed_view.py`
- Test: `streamlit_app/tests/test_feed_view.py`

- [ ] **Step 1: Create `streamlit_app/components/feed_view.py`**

```python
import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.cards import render_alert_card

def render_feed_view(client: APIClient):
    """Render proactive AI feeds & notifications."""
    st.header("⚡ Proactive AI Feeds & Alerts")
    st.caption("AI-generated alerts, candidate updates, and recommended recruiter actions.")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Feed", use_container_width=True):
            st.rerun()

    alerts = client.get_proactive_alerts()

    if not alerts:
        st.info("No active alerts at this time. Everything is up to date!")
        return

    st.write(f"Showing **{len(alerts)}** proactive notifications:")

    for alert in alerts:
        render_alert_card(alert)
```

- [ ] **Step 2: Commit Task 2**

```bash
git add streamlit_app/components/feed_view.py
git commit -m "feat(streamlit): add feed_view component"
```

---

### Task 3: Candidate Pipeline Kanban View (`streamlit_app/components/pipeline_view.py`)

**Files:**
- Create: `streamlit_app/components/pipeline_view.py`

- [ ] **Step 1: Create `streamlit_app/components/pipeline_view.py`**

```python
import streamlit as st
from streamlit_app.api_client import APIClient

PIPELINE_STAGES = [
    "sourced",
    "in_review",
    "submitted",
    "interview",
    "offer",
    "hired",
    "rejected",
]

def render_pipeline_view(client: APIClient):
    """Render Candidate Pipeline Kanban / stage columns."""
    st.header("📊 Candidate Pipeline")
    st.caption("Manage candidate status transitions across pipeline stages.")

    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search candidates by name or email...", key="pipeline_search")
    with col_filter:
        selected_stage = st.selectbox("Stage Filter", options=["All"] + PIPELINE_STAGES, key="pipeline_filter")

    candidates = client.get_candidates(limit=100)

    if search_query:
        q = search_query.lower()
        candidates = [
            c for c in candidates
            if q in f"{c.get('first_name', '')} {c.get('last_name', '')}".lower() or q in c.get('email', '').lower()
        ]

    if selected_stage != "All":
        candidates = [c for c in candidates if c.get("status", "").lower() == selected_stage.lower()]

    if not candidates:
        st.info("No candidates found matching the criteria.")
        return

    st.write(f"Displaying **{len(candidates)}** candidate(s):")

    for cand in candidates:
        cid = str(cand.get("id"))
        cname = f"{cand.get('first_name', '')} {cand.get('last_name', '')}".strip() or "Unnamed Candidate"
        cemail = cand.get("email", "N/A")
        cstatus = cand.get("status", "sourced")

        with st.container(border=True):
            cols = st.columns([3, 2, 2])
            with cols[0]:
                st.markdown(f"**👤 {cname}**")
                st.caption(f"📧 {cemail}")
            with cols[1]:
                st.markdown(f"**Status:** `{cstatus.upper()}`")
            with cols[2]:
                current_idx = PIPELINE_STAGES.index(cstatus.lower()) if cstatus.lower() in PIPELINE_STAGES else 0
                new_status = st.selectbox(
                    "Move Stage",
                    options=PIPELINE_STAGES,
                    index=current_idx,
                    key=f"stage_select_{cid}",
                )
                if new_status.lower() != cstatus.lower():
                    if st.button("Update Stage", key=f"btn_update_{cid}", type="primary"):
                        success = client.update_candidate_status(cid, new_status.lower())
                        if success:
                            st.success(f"Updated {cname} status to {new_status}!")
                            st.rerun()
                        else:
                            st.error("Failed to update status.")
```

- [ ] **Step 2: Commit Task 3**

```bash
git add streamlit_app/components/pipeline_view.py
git commit -m "feat(streamlit): add candidate pipeline_view component"
```

---

### Task 4: Preferences View & Main Navigation Wiring

**Files:**
- Create: `streamlit_app/components/preferences_view.py`
- Modify: `streamlit_app/app.py`

- [ ] **Step 1: Create `streamlit_app/components/preferences_view.py`**

```python
import streamlit as st
from streamlit_app.api_client import APIClient

def render_preferences_view(client: APIClient):
    """Render recruiter preferences and criteria controls."""
    st.header("⚙️ Recruiter Preferences")
    st.caption("Customize your AI recruiter candidate matching weights and automation settings.")

    prefs_data = client.get_preferences()
    explicit = prefs_data.get("explicit", {}) if isinstance(prefs_data, dict) else {}

    with st.form("preferences_form"):
        st.subheader("Sourcing Criteria")
        min_exp = st.number_input(
            "Minimum Years of Experience",
            min_value=0,
            max_value=30,
            value=int(explicit.get("min_years_experience", 3)),
        )
        required_skills = st.text_input(
            "Required Skills (comma-separated)",
            value=", ".join(explicit.get("required_skills", ["Java", "AWS", "Python"])),
        )
        remote_pref = st.checkbox(
            "Prioritize Remote Candidates",
            value=bool(explicit.get("remote_preferred", True)),
        )

        submitted = st.form_submit_button("Save Preferences", type="primary")
        if submitted:
            skills_list = [s.strip() for s in required_skills.split(",") if s.strip()]
            updated_explicit = {
                "min_years_experience": min_exp,
                "required_skills": skills_list,
                "remote_preferred": remote_pref,
            }
            res = client.update_preferences(updated_explicit)
            if res:
                st.success("Preferences updated successfully!")
            else:
                st.error("Failed to update preferences.")
```

- [ ] **Step 2: Update `streamlit_app/app.py` to add tab navigation**

```python
import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.chat_view import render_chat_view
from streamlit_app.components.feed_view import render_feed_view
from streamlit_app.components.pipeline_view import render_pipeline_view
from streamlit_app.components.preferences_view import render_preferences_view

st.set_page_config(
    page_title="ATS AI - Recruiter Portal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    client = APIClient()
    render_sidebar(client)

    # Top-level Portal Tabs
    tab_chat, tab_feed, tab_pipeline, tab_prefs = st.tabs([
        "💬 Conversations",
        "⚡ Feeds & Alerts",
        "📊 Candidate Pipeline",
        "⚙️ Preferences",
    ])

    with tab_chat:
        render_chat_view(client)

    with tab_feed:
        render_feed_view(client)

    with tab_pipeline:
        render_pipeline_view(client)

    with tab_prefs:
        render_preferences_view(client)

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run py_compile verification**

Run: `backend/.venv/bin/python -m py_compile streamlit_app/app.py streamlit_app/components/*.py`

- [ ] **Step 4: Commit Task 4**

```bash
git add streamlit_app/
git commit -m "feat(streamlit): complete full portal tab navigation with feeds, pipeline, and preferences"
```
