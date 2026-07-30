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

    with st.expander("➕ **Create New Job Opening**", expanded=False):
        with st.form("create_job_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                title = st.text_input("Job Title *", placeholder="e.g. Senior Backend Engineer")
                company = st.text_input("Company / Client Name *", placeholder="e.g. Enterprise Cloud Inc.")
                email = st.text_input("Hiring Contact Email *", placeholder="e.g. recruiter@company.com")
                location = st.text_input("Location", placeholder="e.g. San Francisco, CA (Hybrid)")
            with c2:
                first_name = st.text_input("Contact First Name", placeholder="e.g. Sarah")
                last_name = st.text_input("Contact Last Name", placeholder="e.g. Connor")
                phone = st.text_input("Contact Phone", placeholder="e.g. +1-555-0192")
                status = st.selectbox("Requisition Status", options=["Active", "Draft", "Closed"])

            description = st.text_area("Job Description & Requirements", placeholder="Enter job summary, key responsibilities, and required tech stack...")

            submit_job = st.form_submit_button("Create Job Opening", type="primary", use_container_width=True)

            if submit_job:
                if not title.strip() or not company.strip() or not email.strip():
                    st.error("Job Title, Company Name, and Contact Email are required.")
                else:
                    payload = {
                        "title": title.strip(),
                        "organization_name": company.strip(),
                        "email": email.strip(),
                        "first_name": first_name.strip() or "Hiring",
                        "last_name": last_name.strip() or "Manager",
                        "phone": phone.strip() or None,
                        "location": location.strip() or None,
                        "description": description.strip() or None,
                        "status": status.lower()
                    }
                    success, res = client.create_client_contact(payload)
                    if success:
                        st.success(f"Job Requisition '{title}' created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create job requisition: {res}")

    col_search, col_status = st.columns([3, 1])
    with col_search:
        search_q = st.text_input("🔍 Search jobs by title, company, or description...", key="jobs_search")
    with col_status:
        status_filter = st.selectbox("Status Filter", options=["All", "Active", "Draft", "Closed"], key="jobs_status_filter")

    # Fetch live client contacts / job openings from backend
    live_contacts = client.get_client_contacts(limit=100)
    live_jobs = []
    for c in live_contacts:
        c_title = c.get("title") or "Open Requisition"
        c_comp = c.get("organization_name") or f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or "Client Organization"
        c_desc = c.get("description") or f"Requisition managed by {c.get('email', '')}"
        c_loc = c.get("location") or "Remote / Flexible"
        c_status = (c.get("status") or "active").capitalize()
        live_jobs.append({
            "id": str(c.get("id")),
            "title": c_title,
            "company": c_comp,
            "location": c_loc,
            "department": "Client Requisition",
            "status": c_status,
            "skills": ["Requirements listed in description"],
            "description": c_desc,
        })

    jobs = live_jobs + SAMPLE_JOBS if live_jobs else SAMPLE_JOBS

    if search_q:
        q = search_q.lower()
        jobs = [
            j for j in jobs
            if q in j["title"].lower()
            or q in j["company"].lower()
            or q in j["description"].lower()
            or any(q in s.lower() for s in j.get("skills", []))
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
                if job.get("skills"):
                    st.markdown(f"**Required Skills:** `{', '.join(job['skills'])}`")

            with col_actions:
                st.markdown(f"**Status:** `:green[{job['status']}]`")
                if st.button("🔎 Source Candidates", key=f"source_job_{job['id']}", type="primary", use_container_width=True):
                    skills_part = f" requiring {', '.join(job['skills'][:3])}" if job.get("skills") else ""
                    prompt = f"Source top candidates for {job['title']} at {job['company']}{skills_part}"
                    st.session_state["session_id"] = None
                    st.session_state["messages"] = []
                    st.session_state["pending_prompt"] = prompt
                    st.session_state["switch_tab"] = "💬 Conversations"
                    st.session_state["view_mode"] = "chat"
                    st.rerun()

