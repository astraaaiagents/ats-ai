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
        req_skills_val = explicit.get("required_skills", ["Java", "AWS", "Python"])
        if isinstance(req_skills_val, list):
            req_skills_str = ", ".join(req_skills_val)
        else:
            req_skills_str = str(req_skills_val)

        required_skills = st.text_input(
            "Required Skills (comma-separated)",
            value=req_skills_str,
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
