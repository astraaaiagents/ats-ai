import streamlit as st
from streamlit_app.api_client import APIClient

PIPELINE_STAGES = [
    "sourced",
    "screening",
    "in_review",
    "submitted",
    "interview",
    "interviewing",
    "offer",
    "placed",
    "hired",
    "rejected",
]

def render_pipeline_view(client: APIClient):
    """Render Candidate Pipeline view."""
    st.header("📊 Candidate Pipeline")
    st.caption("Manage candidate status transitions across pipeline stages.")

    col_search, col_filter, col_refresh = st.columns([3, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search candidates by name or email...", key="pipeline_search")
    with col_filter:
        selected_stage = st.selectbox("Stage Filter", options=["All"] + PIPELINE_STAGES, key="pipeline_filter")
    with col_refresh:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    candidates = client.get_candidates(limit=100)

    if search_query:
        q = search_query.lower()
        candidates = [
            c for c in candidates
            if q in f"{c.get('first_name', '')} {c.get('last_name', '')}".lower() or q in c.get('email', '').lower()
        ]

    if selected_stage != "All":
        candidates = [c for c in candidates if str(c.get("status", "")).lower() == selected_stage.lower()]

    if not candidates:
        st.info("No candidates found matching the criteria.")
        return

    st.write(f"Displaying **{len(candidates)}** candidate(s):")

    for cand in candidates:
        cid = str(cand.get("id"))
        cname = f"{cand.get('first_name', '')} {cand.get('last_name', '')}".strip() or "Unnamed Candidate"
        cemail = cand.get("email", "N/A")
        ctitle = cand.get("current_title", "")
        company = cand.get("current_employer", "")
        clocation = cand.get("location", "")
        cstatus = str(cand.get("status", "sourced"))
        cskills = cand.get("skills", [])

        sub_info = " | ".join(filter(None, [ctitle, company, clocation]))

        with st.container(border=True):
            cols = st.columns([3, 2, 2])
            with cols[0]:
                st.markdown(f"**👤 {cname}**")
                if sub_info:
                    st.markdown(f"💼 *{sub_info}*")
                st.caption(f"📧 {cemail}")
                if cskills:
                    st.markdown(f"**Skills:** `{', '.join(cskills[:4])}`")
            with cols[1]:
                st.markdown(f"**Status:** `{cstatus.upper()}`")
                if st.button("💼 Search Related Jobs", key=f"btn_jobs_{cid}", type="secondary", use_container_width=True):
                    skills_str = f" with skills: {', '.join(cskills[:3])}" if cskills else ""
                    prompt = f"Search active job requisitions and match suitable open roles for candidate {cname} ({ctitle}){skills_str}"
                    st.session_state["pending_prompt"] = prompt
                    st.session_state["switch_tab"] = "💬 Conversations"
                    st.session_state["active_tab"] = "💬 Conversations"
                    st.session_state["view_mode"] = "chat"
                    st.rerun()

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
