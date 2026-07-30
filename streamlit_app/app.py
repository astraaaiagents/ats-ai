import sys
from pathlib import Path

# Ensure project root is in sys.path when running 'streamlit run streamlit_app/app.py'
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.chat_view import render_chat_view
from streamlit_app.components.feed_view import render_feed_view
from streamlit_app.components.pipeline_view import render_pipeline_view
from streamlit_app.components.jobs_view import render_jobs_view
from streamlit_app.components.preferences_view import render_preferences_view

st.set_page_config(
    page_title="ATS AI - Recruiter Portal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

TABS = [
    "💬 Conversations",
    "⚡ Feeds & Alerts",
    "📊 Candidate Pipeline",
    "💼 Job Openings",
    "⚙️ Preferences",
]

def main():
    client = APIClient()
    render_sidebar(client)

    if "active_tab" not in st.session_state or st.session_state["active_tab"] not in TABS:
        st.session_state["active_tab"] = "💬 Conversations"

    if "nav_segmented_control" not in st.session_state:
        st.session_state["nav_segmented_control"] = st.session_state["active_tab"]

    # Top-level Portal Tab Navigation
    selected_tab = st.segmented_control(
        "Portal Navigation",
        options=TABS,
        selection_mode="single",
        key="nav_segmented_control",
        label_visibility="collapsed",
    )

    if selected_tab:
        st.session_state["active_tab"] = selected_tab

    active = st.session_state.get("active_tab", "💬 Conversations")

    if active == "💬 Conversations":
        render_chat_view(client)
    elif active == "⚡ Feeds & Alerts":
        render_feed_view(client)
    elif active == "📊 Candidate Pipeline":
        render_pipeline_view(client)
    elif active == "💼 Job Openings":
        render_jobs_view(client)
    elif active == "⚙️ Preferences":
        render_preferences_view(client)

if __name__ == "__main__":
    main()
