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
