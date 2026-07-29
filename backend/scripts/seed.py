"""Sample data seeder for the ATS AI application.

Populates the database with:
- 1 organization
- 1 recruiter user
- 1 platform super_admin user
- 10 sample candidates with skills
- 5 sample proactive alerts
- 3 sample conversation sessions with messages
- 2 sample preference records

Usage:
    python -m backend.scripts.seed
    or
    cd backend && python scripts/seed.py
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, Base, engine
from app.models.organization import Organization
from app.models.user import User
from app.models.platform_user import PlatformUser
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.agent_alert import AgentProactiveAlert
from app.models.agent_conversation import AgentConversationSession, AgentConversationMessage
from app.models.recruiter_preference import RecruiterPreference
from app.models.client_contact import ClientContact
from app.auth.password import hash_password


# ── Sample Data ──────────────────────────────────────────────────────

ORGANIZATION = {
    "name": "ATS Recruiting",
    "slug": "ats-recruiting",
}

RECRUITER = {
    "email": "recruiter@example.com",
    "password": "recruiter123",
    "role": "recruiter",
}

PLATFORM_ADMIN = {
    "email": "admin@example.com",
    "password": "admin123",
    "role": "super_admin",
}

CANDIDATES = [
    {
        "first_name": "Alex",
        "last_name": "Johnson",
        "email": "alex.johnson@email.com",
        "phone": "+1 (555) 123-4567",
        "current_title": "Senior Full-Stack Engineer",
        "current_employer": "TechCorp",
        "location": "San Francisco, CA",
        "salary_expectation_min": 170000,
        "salary_expectation_max": 220000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "linkedin",
        "status": "sourced",
        "ai_summary": "Strong full-stack engineer with 7 years of experience in React, TypeScript, and Node.js. Led teams of 4+ engineers.",
        "skills": [
            {"skill_name": "React", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "TypeScript", "proficiency": 5, "years_experience": 4.0},
            {"skill_name": "Node.js", "proficiency": 4, "years_experience": 5.0},
            {"skill_name": "AWS", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "Docker", "proficiency": 3, "years_experience": 2.0},
        ],
    },
    {
        "first_name": "Maria",
        "last_name": "Chen",
        "email": "maria.chen@email.com",
        "phone": "+1 (555) 234-5678",
        "current_title": "Backend Engineer",
        "current_employer": "DataFlow Inc",
        "location": "New York, NY",
        "salary_expectation_min": 160000,
        "salary_expectation_max": 200000,
        "visa_status": "Green Card",
        "notice_period_days": 30,
        "source": "referral",
        "ai_summary": "Experienced backend engineer specializing in Go and distributed systems. Strong PostgreSQL and cloud infrastructure skills.",
        "skills": [
            {"skill_name": "Go", "proficiency": 5, "years_experience": 6.0},
            {"skill_name": "PostgreSQL", "proficiency": 4, "years_experience": 5.0},
            {"skill_name": "Docker", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "Kubernetes", "proficiency": 3, "years_experience": 2.0},
            {"skill_name": "gRPC", "proficiency": 4, "years_experience": 3.0},
        ],
    },
    {
        "first_name": "James",
        "last_name": "Wilson",
        "email": "james.wilson@email.com",
        "phone": "+1 (555) 345-6789",
        "current_title": "DevOps Lead",
        "current_employer": "CloudScale",
        "location": "Austin, TX",
        "salary_expectation_min": 180000,
        "salary_expectation_max": 230000,
        "visa_status": "US Citizen",
        "notice_period_days": 21,
        "source": "agency_db",
        "ai_summary": "DevOps leader with deep Kubernetes and Terraform expertise. Managed infrastructure for 500+ microservices.",
        "skills": [
            {"skill_name": "Kubernetes", "proficiency": 5, "years_experience": 6.0},
            {"skill_name": "Terraform", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "AWS", "proficiency": 5, "years_experience": 7.0},
            {"skill_name": "Docker", "proficiency": 5, "years_experience": 6.0},
            {"skill_name": "Python", "proficiency": 4, "years_experience": 4.0},
        ],
    },
    {
        "first_name": "Priya",
        "last_name": "Patel",
        "email": "priya.patel@email.com",
        "phone": "+1 (555) 456-7890",
        "current_title": "Data Engineer",
        "current_employer": "Analytics Co",
        "location": "Seattle, WA",
        "salary_expectation_min": 150000,
        "salary_expectation_max": 190000,
        "visa_status": "H1B",
        "notice_period_days": 30,
        "source": "linkedin",
        "ai_summary": "Data engineer with strong Python and Spark experience. Built real-time data pipelines processing 10M+ events/day.",
        "skills": [
            {"skill_name": "Python", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "Spark", "proficiency": 4, "years_experience": 4.0},
            {"skill_name": "AWS", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "SQL", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "Airflow", "proficiency": 4, "years_experience": 3.0},
        ],
    },
    {
        "first_name": "Tom",
        "last_name": "Baker",
        "email": "tom.baker@email.com",
        "phone": "+1 (555) 567-8901",
        "current_title": "Frontend Engineer",
        "current_employer": "DesignTech",
        "location": "Portland, OR",
        "salary_expectation_min": 140000,
        "salary_expectation_max": 170000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "github",
        "ai_summary": "Frontend specialist with React and Vue expertise. Strong UI/UX sensibility with 4 years of experience.",
        "skills": [
            {"skill_name": "React", "proficiency": 5, "years_experience": 4.0},
            {"skill_name": "Vue", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "TypeScript", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "CSS", "proficiency": 5, "years_experience": 4.0},
            {"skill_name": "JavaScript", "proficiency": 5, "years_experience": 4.0},
        ],
    },
    {
        "first_name": "Sarah",
        "last_name": "Kim",
        "email": "sarah.kim@email.com",
        "phone": "+1 (555) 678-9012",
        "current_title": "ML Engineer",
        "current_employer": "AI Labs",
        "location": "San Francisco, CA",
        "salary_expectation_min": 190000,
        "salary_expectation_max": 250000,
        "visa_status": "Green Card",
        "notice_period_days": 30,
        "source": "linkedin",
        "ai_summary": "ML engineer with PyTorch and production ML systems experience. Published 3 papers on NLP.",
        "skills": [
            {"skill_name": "Python", "proficiency": 5, "years_experience": 6.0},
            {"skill_name": "PyTorch", "proficiency": 5, "years_experience": 4.0},
            {"skill_name": "AWS", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "Docker", "proficiency": 3, "years_experience": 2.0},
            {"skill_name": "TensorFlow", "proficiency": 4, "years_experience": 3.0},
        ],
    },
    {
        "first_name": "David",
        "last_name": "Rodriguez",
        "email": "david.rodriguez@email.com",
        "phone": "+1 (555) 789-0123",
        "current_title": "Java Lead",
        "current_employer": "Enterprise Solutions",
        "location": "Chicago, IL",
        "salary_expectation_min": 175000,
        "salary_expectation_max": 215000,
        "visa_status": "US Citizen",
        "notice_period_days": 21,
        "source": "referral",
        "ai_summary": "Java lead with 10 years of enterprise experience. Microservices, Spring Boot, and team leadership.",
        "skills": [
            {"skill_name": "Java", "proficiency": 5, "years_experience": 10.0},
            {"skill_name": "Spring Boot", "proficiency": 5, "years_experience": 7.0},
            {"skill_name": "Microservices", "proficiency": 4, "years_experience": 5.0},
            {"skill_name": "PostgreSQL", "proficiency": 4, "years_experience": 6.0},
            {"skill_name": "AWS", "proficiency": 3, "years_experience": 3.0},
        ],
    },
    {
        "first_name": "Emily",
        "last_name": "Zhang",
        "email": "emily.zhang@email.com",
        "phone": "+1 (555) 890-1234",
        "current_title": "Senior Python Engineer",
        "current_employer": "FinTech Corp",
        "location": "New York, NY",
        "salary_expectation_min": 165000,
        "salary_expectation_max": 205000,
        "visa_status": "H1B",
        "notice_period_days": 30,
        "source": "agency_db",
        "ai_summary": "Senior Python engineer with FinTech domain expertise. FastAPI, async programming, and high-throughput systems.",
        "skills": [
            {"skill_name": "Python", "proficiency": 5, "years_experience": 7.0},
            {"skill_name": "FastAPI", "proficiency": 5, "years_experience": 3.0},
            {"skill_name": "PostgreSQL", "proficiency": 4, "years_experience": 5.0},
            {"skill_name": "Docker", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "Redis", "proficiency": 4, "years_experience": 3.0},
        ],
    },
    {
        "first_name": "Michael",
        "last_name": "Brown",
        "email": "michael.brown@email.com",
        "phone": "+1 (555) 901-2345",
        "current_title": "Cloud Architect",
        "current_employer": "CloudFirst",
        "location": "Denver, CO",
        "salary_expectation_min": 200000,
        "salary_expectation_max": 260000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "linkedin",
        "ai_summary": "Cloud architect with AWS and Azure certifications. 12 years of infrastructure and architecture experience.",
        "skills": [
            {"skill_name": "AWS", "proficiency": 5, "years_experience": 8.0},
            {"skill_name": "Azure", "proficiency": 4, "years_experience": 4.0},
            {"skill_name": "Terraform", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "Kubernetes", "proficiency": 4, "years_experience": 4.0},
            {"skill_name": "Python", "proficiency": 4, "years_experience": 5.0},
        ],
    },
    {
        "first_name": "Lisa",
        "last_name": "Nguyen",
        "email": "lisa.nguyen@email.com",
        "phone": "+1 (555) 012-3456",
        "current_title": "React Native Developer",
        "current_employer": "MobileFirst",
        "location": "San Jose, CA",
        "salary_expectation_min": 145000,
        "salary_expectation_max": 180000,
        "visa_status": "Green Card",
        "notice_period_days": 21,
        "source": "github",
        "ai_summary": "Mobile developer specializing in React Native. Built 5+ apps with 100K+ downloads.",
        "skills": [
            {"skill_name": "React Native", "proficiency": 5, "years_experience": 4.0},
            {"skill_name": "React", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "TypeScript", "proficiency": 4, "years_experience": 3.0},
            {"skill_name": "JavaScript", "proficiency": 5, "years_experience": 5.0},
            {"skill_name": "iOS", "proficiency": 3, "years_experience": 2.0},
        ],
    },
]

ALERTS = [
    {
        "alert_type": "new_match",
        "title": "3 new candidates match TCS — Java Lead",
        "body": "David Rodriguez (95%), Alex Johnson (82%), Emily Zhang (70%) match your criteria.",
        "is_read": False,
    },
    {
        "alert_type": "pipeline_update",
        "title": "Pipeline for Infosys — Python Senior is thin",
        "body": "Only 2 candidates in the pipeline. Consider expanding your search criteria.",
        "is_read": False,
    },
    {
        "alert_type": "feedback_reminder",
        "title": "Review pending candidates",
        "body": "You have 5 candidates awaiting your review from this week's sourcing pulse.",
        "is_read": True,
    },
    {
        "alert_type": "weekly_digest",
        "title": "Weekly learning summary ready",
        "body": "Your agent learned 3 new preference patterns this week. Review in Preferences tab.",
        "is_read": True,
    },
    {
        "alert_type": "new_match",
        "title": "Strong match found for Wipro — Data Engineer",
        "body": "Priya Patel (88%) and Sarah Kim (75%) match your data engineer criteria.",
        "is_read": False,
    },
]

CLIENT_CONTACTS = [
    {"email": "john.smith@acmecorp.com", "first_name": "John", "last_name": "Smith", "phone": "+1 (555) 100-2001", "organization_name": "Acme Corp", "title": "Senior Java Developer", "location": "New York, NY", "description": "Looking for a senior Java developer with Spring Boot experience"},
    {"email": "sarah.jones@techstart.io", "first_name": "Sarah", "last_name": "Jones", "phone": "+1 (555) 100-2002", "organization_name": "TechStart.io", "title": "React Frontend Engineer", "location": "San Francisco, CA", "description": "Frontend engineer for our design system team"},
    {"email": "mike.chen@globalfin.com", "first_name": "Mike", "last_name": "Chen", "phone": "+1 (555) 100-2003", "organization_name": "GlobalFin", "title": "Data Engineer - Python", "location": "Chicago, IL", "description": "Build real-time data pipelines for trading systems"},
    {"email": "lisa.patel@datawise.co", "first_name": "Lisa", "last_name": "Patel", "phone": "+1 (555) 100-2004", "organization_name": "DataWise", "title": "ML Platform Engineer", "location": "Remote", "description": "Build ML infrastructure and model serving platform"},
    {"email": "rob.taylor@cloudnine.dev", "first_name": "Rob", "last_name": "Taylor", "phone": "+1 (555) 100-2005", "organization_name": "CloudNine.dev", "title": "DevOps/SRE Lead", "location": "Austin, TX", "description": "Lead our SRE team managing 500+ microservices"},
]


async def seed_database():
    """Create all tables and insert sample data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # ── Organization ───────────────────────────────────────────
        org = await session.execute(
            select(Organization).where(Organization.slug == ORGANIZATION["slug"])
        )
        org = org.scalar_one_or_none()
        if not org:
            org = Organization(**ORGANIZATION)
            session.add(org)
            await session.flush()
            print(f"Created organization: {org.name} (id={org.id})")
        else:
            print(f"Organization already exists: {org.name} (id={org.id})")

        org_id = org.id

        # ── Platform Admin ─────────────────────────────────────────
        admin = await session.execute(
            select(PlatformUser).where(PlatformUser.email == PLATFORM_ADMIN["email"])
        )
        admin = admin.scalar_one_or_none()
        if not admin:
            admin = PlatformUser(
                email=PLATFORM_ADMIN["email"],
                password_hash=hash_password(PLATFORM_ADMIN["password"]),
                role=PLATFORM_ADMIN["role"],
            )
            session.add(admin)
            await session.flush()
            print(f"Created platform admin: {admin.email} (id={admin.id})")
        else:
            print(f"Platform admin already exists: {admin.email}")

        # ── Recruiter User ─────────────────────────────────────────
        user = await session.execute(
            select(User).where(User.email == RECRUITER["email"])
        )
        user = user.scalar_one_or_none()
        if not user:
            user = User(
                email=RECRUITER["email"],
                password_hash=hash_password(RECRUITER["password"]),
                role=RECRUITER["role"],
                organization_id=org_id,
            )
            session.add(user)
            await session.flush()
            print(f"Created recruiter: {user.email} (id={user.id})")
        else:
            print(f"Recruiter already exists: {user.email}")

        user_id = user.id

        # ── Candidates ─────────────────────────────────────────────
        existing_emails = set()
        result = await session.execute(select(Candidate.email))
        for row in result.scalars():
            existing_emails.add(row)

        for i, c_data in enumerate(CANDIDATES):
            if c_data["email"] in existing_emails:
                print(f"Candidate {c_data['first_name']} {c_data['last_name']} already exists")
                continue

            candidate = Candidate(
                organization_id=org_id,
                owner_id=user_id,
                **{k: v for k, v in c_data.items() if k != "skills"},
            )
            session.add(candidate)
            await session.flush()

            for skill_data in c_data["skills"]:
                skill = CandidateSkill(
                    organization_id=org_id,
                    candidate_id=candidate.id,
                    **skill_data,
                )
                session.add(skill)

            existing_emails.add(c_data["email"])
            print(f"Created candidate: {candidate.first_name} {candidate.last_name} ({candidate.email})")

        # ── Proactive Alerts ───────────────────────────────────────
        for i, a_data in enumerate(ALERTS):
            alert = AgentProactiveAlert(
                recruiter_id=user_id,
                **a_data,
            )
            session.add(alert)
            print(f"Created alert: {a_data['title']}")

        # ── Conversation Sessions ──────────────────────────────────
        now = datetime.now(timezone.utc)
        sessions_data = [
            {
                "title": "Candidate Sourcing",
                "messages": [
                    {"role": "user", "content": "Find me Java developers in San Francisco"},
                    {"role": "agent", "content": "I found 3 Java developers in the San Francisco area. David Rodriguez (95% match) and Alex Johnson (82% match) look strong.", "confidence": 0.88},
                    {"role": "user", "content": "Submit David Rodriguez for the TCS role"},
                    {"role": "agent", "content": "Submitted David Rodriguez for TCS — Java Lead. Status updated to submitted.", "confidence": 0.95},
                ],
            },
            {
                "title": "Pipeline Review",
                "messages": [
                    {"role": "user", "content": "How's the pipeline looking for Python Senior?"},
                    {"role": "agent", "content": "The pipeline for Infosys — Python Senior has 2 candidates. Emily Zhang (85%) and Maria Chen (72%). The pipeline is thin — I recommend expanding the search.", "confidence": 0.82},
                ],
            },
            {
                "title": "Preference Update",
                "messages": [
                    {"role": "user", "content": "I want candidates with AWS experience and notice period under 30 days"},
                    {"role": "agent", "content": "Updated your preferences: AWS experience required, notice period ≤ 30 days. This will affect future candidate matching.", "confidence": 0.97},
                ],
            },
        ]

        for s_data in sessions_data:
            session_obj = AgentConversationSession(
                recruiter_id=user_id,
                title=s_data["title"],
            )
            session.add(session_obj)
            await session.flush()

            for m_data in s_data["messages"]:
                msg = AgentConversationMessage(
                    session_id=session_obj.id,
                    role=m_data["role"],
                    content=m_data["content"],
                    confidence=m_data.get("confidence"),
                    created_at=now - timedelta(hours=len(sessions_data) * 2 + 1),
                )
                session.add(msg)

            print(f"Created session: {s_data['title']}")

        # ── Preferences ────────────────────────────────────────────
        pref = RecruiterPreference(
            recruiter_id=user_id,
            explicit_preferences={
                "required_skills": ["Python", "AWS", "PostgreSQL"],
                "preferred_location": "San Francisco, CA",
                "min_experience_years": 5,
                "max_notice_period_days": 30,
                "salary_range_min": 150000,
                "salary_range_max": 220000,
            },
            implicit_preference_vector=[0.85, 0.78, 0.55, 0.35] + [0.0] * 1532,  # 1536-dim vector
        )
        session.add(pref)
        print("Created recruiter preferences")

        # ── Client Contacts (Jobs) ─────────────────────────────────
        existing_emails = set()
        result = await session.execute(select(ClientContact.email))
        for row in result.scalars():
            existing_emails.add(row)

        for c_data in CLIENT_CONTACTS:
            if c_data["email"] in existing_emails:
                print(f"Contact {c_data['first_name']} {c_data['last_name']} already exists")
                continue
            contact = ClientContact(
                organization_id=org_id,
                **c_data,
                status="active",
            )
            session.add(contact)
            existing_emails.add(c_data["email"])
            print(f"Created contact: {contact.organization_name} — {contact.title}")

        await session.commit()
        print("\n✅ Seed complete!")
        print(f"\nLogin credentials:")
        print(f"  Recruiter: {RECRUITER['email']} / {RECRUITER['password']}")
        print(f"  Admin:     {PLATFORM_ADMIN['email']} / {PLATFORM_ADMIN['password']}")


if __name__ == "__main__":
    asyncio.run(seed_database())
