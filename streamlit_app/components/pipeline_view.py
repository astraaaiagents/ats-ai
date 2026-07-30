import streamlit as st
from streamlit_app.api_client import APIClient

PIPELINE_STAGES = [
    "sourced",
    "in_review",
    "submitted",
    "interviewing",
    "shortlisted",
    "offer_extended",
    "placed",
    "rejected",
]

def _extract_skill_names(skills) -> list[str]:
    """Extract list of skill string names whether skills are dicts or strings."""
    names = []
    for s in skills:
        if isinstance(s, dict):
            val = s.get("name") or s.get("skill_name") or s.get("title") or ""
            if val:
                names.append(str(val))
        elif isinstance(s, str) and s.strip():
            names.append(s.strip())
        elif s:
            names.append(str(s))
    return names

def render_pipeline_view(client: APIClient):
    """Render Candidate Pipeline view."""
    st.header("📊 Candidate Pipeline")
    st.caption("Manage candidate status transitions across pipeline stages.")

    with st.expander("➕ **Add New Candidate**", expanded=False):
        with st.form("create_candidate_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("First Name *")
                email = st.text_input("Email *")
                current_title = st.text_input("Current Title")
                location = st.text_input("Location (e.g. San Francisco, CA)")
                salary_min = st.number_input("Salary Expectation Min ($)", min_value=0, value=0, step=10000)
            with c2:
                last_name = st.text_input("Last Name *")
                phone = st.text_input("Phone Number")
                current_employer = st.text_input("Current Employer")
                visa_status = st.selectbox("Visa Status", options=["US Citizen", "Green Card", "H1B", "L1", "TN", "Other"])
                salary_max = st.number_input("Salary Expectation Max ($)", min_value=0, value=0, step=10000)

            skills_input = st.text_input("Skills (comma-separated, e.g. Python, FastAPI, Docker, PostgreSQL)")
            ai_summary = st.text_area("Candidate Summary / Notes")

            submit_cand = st.form_submit_button("Create Candidate", type="primary", use_container_width=True)

            if submit_cand:
                if not first_name.strip() or not last_name.strip() or not email.strip():
                    st.error("First Name, Last Name, and Email are required.")
                else:
                    skills_list = []
                    if skills_input.strip():
                        for sk in skills_input.split(","):
                            sk_str = sk.strip()
                            if sk_str:
                                skills_list.append({"skill_name": sk_str, "proficiency": 3})

                    payload = {
                        "first_name": first_name.strip(),
                        "last_name": last_name.strip(),
                        "email": email.strip(),
                        "phone": phone.strip() or None,
                        "current_title": current_title.strip() or None,
                        "current_employer": current_employer.strip() or None,
                        "location": location.strip() or None,
                        "visa_status": visa_status,
                        "salary_expectation_min": salary_min if salary_min > 0 else None,
                        "salary_expectation_max": salary_max if salary_max > 0 else None,
                        "ai_summary": ai_summary.strip() or None,
                        "skills": skills_list,
                        "source": "streamlit_portal",
                        "status": "sourced"
                    }
                    success, res = client.create_candidate(payload)
                    if success:
                        st.success(f"Candidate {first_name} {last_name} created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create candidate: {res}")

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
        cstatus = str(cand.get("status", "sourced")).lower()
        skill_names = _extract_skill_names(cand.get("skills", []))

        sub_info = " | ".join(filter(None, [ctitle, company, clocation]))

        with st.container(border=True):
            cols = st.columns([3, 2.5, 2])
            with cols[0]:
                st.markdown(f"**👤 {cname}**")
                if sub_info:
                    st.markdown(f"💼 *{sub_info}*")
                st.caption(f"📧 {cemail}")
                if skill_names:
                    st.markdown(f"**Skills:** `{', '.join(skill_names[:4])}`")
            with cols[1]:
                st.markdown(f"**Status:** `{cstatus.upper()}`")
                st.write("")
                if st.button("💼 Search Related Jobs", key=f"btn_jobs_{cid}", type="primary", use_container_width=True):
                    skills_str = f" with skills: {', '.join(skill_names[:3])}" if skill_names else ""
                    prompt = f"Search active job requisitions and match suitable open roles for candidate {cname} ({ctitle}){skills_str}"
                    st.session_state["session_id"] = None
                    st.session_state["messages"] = []
                    st.session_state["pending_prompt"] = prompt
                    st.session_state["switch_tab"] = "💬 Conversations"
                    st.session_state["view_mode"] = "chat"
                    st.rerun()

            with cols[2]:
                current_idx = PIPELINE_STAGES.index(cstatus) if cstatus in PIPELINE_STAGES else 0
                new_status = st.selectbox(
                    "Move Stage",
                    options=PIPELINE_STAGES,
                    index=current_idx,
                    key=f"stage_select_{cid}",
                )
                if new_status.lower() != cstatus:
                    if st.button("Update Stage", key=f"btn_update_{cid}", type="secondary"):
                        success, err_msg = client.update_candidate_status(cid, new_status.lower())
                        if success:
                            st.success(f"Updated {cname} status to {new_status}!")
                            st.rerun()
                        else:
                            st.error(f"Failed to update status: {err_msg}")
