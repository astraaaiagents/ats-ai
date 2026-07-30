import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.cards import render_job_card

# Default Requisitions / Openings
SAMPLE_JOBS = [
    {
        "id": "job-101",
        "title": "Senior Java Backend Engineer",
        "company": "Enterprise Cloud Solutions",
        "location": "Remote / San Francisco, CA",
        "department": "Engineering",
        "status": "Active",
        "skills": ["Java", "Spring Boot", "AWS", "Microservices", "PostgreSQL"],
        "description": "Looking for a Senior Java Backend Engineer with 5+ years of experience in high-throughput cloud architectures and Spring Boot.",
    },
    {
        "id": "job-102",
        "title": "Lead MLOps Engineer",
        "company": "AI Innovations",
        "location": "New York, NY (Hybrid)",
        "department": "AI & Analytics",
        "status": "Active",
        "skills": ["Python", "PyTorch", "Kubernetes", "MLflow", "AWS"],
        "description": "Lead MLOps engineer to design, deploy, and monitor scalable ML pipelines and LLM agent infrastructure.",
    },
    {
        "id": "job-103",
        "title": "Full Stack React / Python Engineer",
        "company": "Fintech Global",
        "location": "Remote",
        "department": "Product Development",
        "status": "Active",
        "skills": ["React", "TypeScript", "FastAPI", "Python", "Docker"],
        "description": "Full stack engineer responsible for high-performance frontend interfaces and async backend APIs.",
    },
    {
        "id": "job-104",
        "title": "Staff Cloud Security Architect",
        "company": "CyberGuard Security",
        "location": "Austin, TX / Remote",
        "department": "Security Operations",
        "status": "Active",
        "skills": ["AWS", "Kubernetes", "IAM", "Terraform", "CI/CD"],
        "description": "Define enterprise cloud security posture, zero-trust policies, and compliance automation.",
    },
]

def render_jobs_view(client: APIClient):
    """Render Job Openings overview and sourcing trigger."""
    st.header("💼 Job Requisitions & Openings")
    st.caption("Active job requisitions and candidate matching automation.")

    col_search, col_status = st.columns([3, 1])
    with col_search:
        search_q = st.text_input("🔍 Search jobs by title, company, or skills...", key="jobs_search")
    with col_status:
        status_filter = st.selectbox("Status", options=["All", "Active", "Draft", "Closed"], key="jobs_status_filter")

    jobs = SAMPLE_JOBS

    if search_q:
        q = search_q.lower()
        jobs = [
            j for j in jobs
            if q in j["title"].lower()
            or q in j["company"].lower()
            or any(q in s.lower() for s in j["skills"])
        ]

    if status_filter != "All":
        jobs = [j for j in jobs if j["status"].lower() == status_filter.lower()]

    if not jobs:
        st.info("No job requisitions found matching the query.")
        return

    st.write(f"Showing **{len(jobs)}** job requisition(s):")

    for job in jobs:
        with st.container(border=True):
            col_main, col_actions = st.columns([3, 1])
            with col_main:
                st.markdown(f"### 💼 {job['title']}")
                st.caption(f"🏢 **{job['company']}** • 📍 {job['location']} • 🏷️ `{job['department']}`")
                st.write(job["description"])
                st.markdown(f"**Required Skills:** `{', '.join(job['skills'])}`")

            with col_actions:
                st.markdown(f"**Status:** `:green[{job['status']}]`")
                if st.button("🔎 Source Candidates", key=f"source_job_{job['id']}", type="primary", use_container_width=True):
                    prompt = f"Source top candidates for {job['title']} requiring {', '.join(job['skills'][:3])}"
                    st.session_state["pending_prompt"] = prompt
                    st.session_state["active_tab"] = "💬 Conversations"
                    st.session_state["nav_segmented_control"] = "💬 Conversations"
                    st.session_state["view_mode"] = "chat"
                    st.rerun()
