import streamlit as st
from typing import Dict, Any

def render_candidate_card(card: Dict[str, Any]):
    """Render structured candidate card."""
    data = card.get("data") if isinstance(card.get("data"), dict) else card

    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()
    name = full_name or data.get("name") or data.get("candidate_name") or card.get("name") or "Candidate"

    title = data.get("current_title") or data.get("title") or card.get("title") or "N/A"
    location = data.get("location") or card.get("location") or ""
    experience = data.get("experience") or data.get("years_experience") or card.get("experience") or "N/A"

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**👤 {name}**")
            sub_info = f"Role: {title}"
            if location:
                sub_info += f" • 📍 {location}"
            if experience != "N/A":
                sub_info += f" • Exp: {experience}"
            st.caption(sub_info)
        with col2:
            score = card.get("fitScore") if card.get("fitScore") is not None else card.get("fit_score", data.get("fitScore", data.get("fit_score")))
            if score is not None:
                try:
                    score_val = float(score)
                    if score_val <= 1.0:
                        score_val = score_val * 100
                    st.metric(label="Fit Score", value=f"{int(score_val)}%")
                except (ValueError, TypeError):
                    st.metric(label="Fit Score", value=str(score))

        skills = data.get("skills") or card.get("skills", [])
        if isinstance(skills, list) and skills:
            st.markdown(f"**Skills:** `{', '.join(skills[:6])}`")

        strengths = card.get("strengths") or data.get("strengths", [])
        if isinstance(strengths, list) and strengths:
            st.caption(f"✅ **Strengths:** {', '.join(strengths)}")

        summary = card.get("summary") or card.get("match_rationale") or data.get("summary")
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
