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
