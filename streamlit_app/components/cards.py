import streamlit as st
from typing import Dict, Any

def render_candidate_card(card: Dict[str, Any]):
    """Render structured candidate card."""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            name = card.get("name") or card.get("candidate_name") or "Candidate"
            title = card.get("title") or card.get("current_title") or "N/A"
            experience = card.get("experience") or card.get("years_experience") or "N/A"
            st.markdown(f"**👤 {name}**")
            st.caption(f"Role: {title} • Exp: {experience}")
        with col2:
            score = card.get("fit_score", card.get("score"))
            if score is not None:
                try:
                    score_val = float(score)
                    if score_val <= 1.0:
                        score_val = score_val * 100
                    st.metric(label="Fit Score", value=f"{int(score_val)}%")
                except (ValueError, TypeError):
                    st.metric(label="Fit Score", value=str(score))

        skills = card.get("skills", [])
        if isinstance(skills, list) and skills:
            st.markdown(f"**Skills:** `{', '.join(skills[:6])}`")

        summary = card.get("summary") or card.get("match_rationale")
        if summary:
            st.write(f"*{summary}*")

def render_job_card(card: Dict[str, Any]):
    """Render structured job card."""
    with st.container(border=True):
        title = card.get("title") or card.get("job_title") or "Job Opening"
        company = card.get("company") or card.get("company_name") or "Internal"
        location = card.get("location") or "Remote"
        st.markdown(f"**💼 {title}**")
        st.caption(f"Company: {company} • Location: {location}")
        if card.get("description"):
            st.write(card["description"])

def render_alert_card(card: Dict[str, Any]):
    """Render proactive alert card."""
    severity = str(card.get("severity") or card.get("priority") or "info").lower()
    icon = "⚠️" if severity in ("warning", "high", "critical") else "ℹ️"
    title = card.get("title") or card.get("alert_type") or "Alert"
    message = card.get("message") or card.get("content") or ""
    with st.container(border=True):
        st.markdown(f"**{icon} {title}**")
        if message:
            st.write(message)
