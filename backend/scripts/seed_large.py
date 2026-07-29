"""Large synthetic data seeder for the ATS AI application.

Generates:
- 50 candidates with skills
- 20 jobs
- 50 agent actions
- 30 proactive alerts
- 10 conversation sessions
- 2 recruiter preferences

Usage:
    cd backend && python scripts/seed_large.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.user import User
from app.models.candidate import Candidate
from app.models.candidate_skill import CandidateSkill
from app.models.agent_action import AgentAction
from app.models.agent_alert import AgentProactiveAlert
from app.models.agent_conversation import AgentConversationSession, AgentConversationMessage
from app.models.recruiter_preference import RecruiterPreference
from app.auth.password import hash_password

# ── Synthetic Data Generators ──────────────────────────────────────────

FIRST_NAMES = [
    "Alex", "Maria", "James", "Priya", "Tom", "Sarah", "David", "Emily",
    "Michael", "Lisa", "Robert", "Jennifer", "William", "Elizabeth",
    "Daniel", "Margaret", "Matthew", "Sandra", "Anthony", "Ashley",
    "Mark", "Dorothy", "Donald", "Kimberly", "Steven", "Michelle",
    "Paul", "Carol", "Andrew", "Amanda", "Joshua", "Melissa", "Kenneth",
    "Deborah", "Kevin", "Susan", "Brian", "Jessica", "George", "Sharon",
    "Timothy", "Laura", "Ronald", "Cynthia", "Edward", "Kathleen",
    "Jason", "Amy", "Jeffrey", "Angela",
]

LAST_NAMES = [
    "Johnson", "Chen", "Wilson", "Patel", "Baker", "Kim", "Rodriguez",
    "Zhang", "Brown", "Nguyen", "Garcia", "Martinez", "Anderson",
    "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson",
    "Lee", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen",
    "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans",
]

COMPANIES = [
    "TechCorp", "DataFlow Inc", "CloudScale", "Analytics Co", "DesignTech",
    "AI Labs", "Enterprise Solutions", "FinTech Corp", "CloudFirst",
    "MobileFirst", "StartupXYZ", "BigTech Inc", "MediaGroup", "AutoDrive",
    "BioGen", "CyberShield", "GreenEnergy", "SpaceTech", "RoboWorks",
    "QuantumSoft", "NeuralNet", "BlockChain Co", "VR Studios", "DroneTech",
]

TITLES = [
    "Senior Full-Stack Engineer", "Backend Engineer", "DevOps Lead",
    "Data Engineer", "Frontend Engineer", "ML Engineer", "Java Lead",
    "Senior Python Engineer", "Cloud Architect", "React Native Developer",
    "Staff Software Engineer", "Principal Engineer", "Engineering Manager",
    "Tech Lead", "Site Reliability Engineer", "Security Engineer",
    "Platform Engineer", "Data Scientist", "AI Research Scientist",
    "Solutions Architect", "Technical Program Manager",
]

SKILLS_POOL = [
    ("Python", 5), ("JavaScript", 5), ("TypeScript", 4), ("React", 5),
    ("Node.js", 4), ("Go", 3), ("Rust", 2), ("Java", 4), ("C++", 2),
    ("SQL", 5), ("PostgreSQL", 4), ("MongoDB", 3), ("Redis", 3),
    ("AWS", 5), ("GCP", 3), ("Azure", 3), ("Docker", 5), ("Kubernetes", 4),
    ("Terraform", 3), ("CI/CD", 4), ("Linux", 5), ("Git", 5),
    ("Machine Learning", 3), ("Deep Learning", 2), ("PyTorch", 2),
    ("TensorFlow", 2), ("Spark", 3), ("Kafka", 3), ("gRPC", 2),
    ("FastAPI", 3), ("Django", 2), ("Vue", 3), ("Angular", 2),
    ("Swift", 2), ("Kotlin", 2), ("Flutter", 2), ("GraphQL", 3),
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Boston, MA", "Denver, CO", "Chicago, IL", "Portland, OR",
    "Los Angeles, CA", "Miami, FL", "Atlanta, GA", "Dallas, TX",
    "Remote", "Hybrid - San Francisco", "Hybrid - New York",
]

VISA_STATUSES = ["US Citizen", "Green Card", "H1B", "O1 Visa", "TN Visa"]

SOURCES = ["linkedin", "github", "referral", "agency_db", "career_site", "job_fair"]

ALERT_TYPES = ["new_match", "pipeline_update", "feedback_reminder", "weekly_digest"]

ACTION_TYPES = ["source", "rank", "outreach", "preference_update", "proactive_alert", "intent_parse"]

AGENT_NAMES = ["orchestrator", "sourcing", "ranking", "outreach", "preference_engine"]

JOB_TITLES = [
    "Senior Python Engineer", "Full-Stack Developer", "Data Engineer",
    "ML Engineer", "DevOps Engineer", "Frontend Engineer",
    "Backend Engineer", "Cloud Architect", "Security Engineer",
    "Platform Engineer", "Staff Software Engineer", "Tech Lead",
    "Engineering Manager", "Site Reliability Engineer", "Data Scientist",
    "AI Research Scientist", "Solutions Architect", "Technical Program Manager",
    "iOS Developer", "Android Developer",
]

COMPANY_NAMES = [
    "TechCorp", "DataFlow Inc", "CloudScale", "Analytics Co", "DesignTech",
    "AI Labs", "Enterprise Solutions", "FinTech Corp", "CloudFirst",
    "MobileFirst", "StartupXYZ", "BigTech Inc", "MediaGroup", "AutoDrive",
    "BioGen", "CyberShield", "GreenEnergy", "SpaceTech", "RoboWorks",
    "QuantumSoft",
]


def random_skill_set():
    """Generate 3-7 random skills for a candidate."""
    num_skills = random.randint(3, 7)
    selected = random.sample(SKILLS_POOL, num_skills)
    return [
        {
            "skill_name": name,
            "proficiency": random.randint(2, 5),
            "years_experience": round(random.uniform(1.0, 10.0), 1),
        }
        for name, _ in selected
    ]


def generate_candidates(count):
    """Generate synthetic candidates."""
    candidates = []
    used_emails = set()
    for i in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}{i}@email.com"
        while email in used_emails:
            i += 1
            email = f"{first.lower()}.{last.lower()}{i}@email.com"
        used_emails.add(email)

        skills = random_skill_set()
        max_exp = max(s["years_experience"] for s in skills)

        candidates.append({
            "first_name": first,
            "last_name": last,
            "email": email,
            "phone": f"+1 (555) {random.randint(100,999)}-{random.randint(1000,9999)}",
            "current_title": random.choice(TITLES),
            "current_employer": random.choice(COMPANIES),
            "location": random.choice(LOCATIONS),
            "salary_expectation_min": random.randint(120000, 200000),
            "salary_expectation_max": random.randint(200000, 300000),
            "visa_status": random.choice(VISA_STATUSES),
            "notice_period_days": random.choice([0, 7, 14, 21, 30, 60]),
            "source": random.choice(SOURCES),
            "status": random.choice(["sourced", "screening", "interview", "offer"]),
            "ai_summary": f"Strong candidate with {int(max_exp)}+ years of experience. Expert in {skills[0]['skill_name']}.",
            "skills": skills,
        })
    return candidates


def generate_agent_actions(count, user_id, session_id):
    """Generate synthetic agent actions."""
    actions = []
    action_templates = [
        ("source", "sourcing", "Searched candidate database for {title} in {location}"),
        ("rank", "ranking", "Ranked {count} candidates for {title} position"),
        ("outreach", "outreach", "Sent outreach message to {name} for {title} role"),
        ("preference_update", "preference_engine", "Updated recruiter preferences: {pref}"),
        ("proactive_alert", "orchestrator", "Generated proactive alert: {alert}"),
        ("intent_parse", "orchestrator", "Parsed recruiter intent: {intent}"),
    ]
    pref_templates = ["AWS required", "Python 5+ years", "Remote preferred", "Senior level only"]
    alert_templates = ["New match found", "Pipeline thin", "Feedback overdue", "Weekly digest ready"]
    intent_templates = ["Find Java developers", "Rank candidates by fit", "Send offers", "Update preferences"]

    for _ in range(count):
        action_type, agent_name, template = random.choice(action_templates)
        content = template.format(
            title=random.choice(JOB_TITLES),
            location=random.choice(LOCATIONS),
            count=random.randint(5, 50),
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            pref=random.choice(pref_templates),
            alert=random.choice(alert_templates),
            intent=random.choice(intent_templates),
        )
        actions.append({
            "recruiter_id": user_id,
            "session_id": session_id,
            "action_type": action_type,
            "agent_name": agent_name,
            "input_pseudonymized": content,
            "output_pseudonymized": f"Action completed: {action_type} by {agent_name}",
        })
    return actions


def generate_alerts(count, user_id):
    """Generate synthetic proactive alerts."""
    alerts = []
    title_templates = [
        "3 new candidates match {title}",
        "Pipeline for {title} is thin",
        "Review pending candidates for {title}",
        "Weekly learning summary ready",
        "Strong match found for {title}",
        "Outreach response received from {name}",
        "Interview scheduled for {name}",
        "Offer extended to {name}",
    ]
    body_templates = [
        "{name} ({score}%) matches your criteria.",
        "Only {count} candidates in the pipeline. Consider expanding search.",
        "You have {count} candidates awaiting your review.",
        "Your agent learned {count} new preference patterns this week.",
        "{name} ({score}%) and {name2} ({score2}%) match your criteria.",
        "{name} responded positively to your outreach.",
        "Interview scheduled for {name} on {date}.",
        "Offer extended to {name} at ${salary}/year.",
    ]

    for _ in range(count):
        title = random.choice(title_templates).format(
            title=random.choice(JOB_TITLES),
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        )
        body = random.choice(body_templates).format(
            name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            name2=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            score=random.randint(60, 98),
            score2=random.randint(50, 85),
            count=random.randint(2, 15),
            date=f"2026-07-{random.randint(20, 28)}",
            salary=random.randint(150000, 280000),
        )
        alerts.append({
            "alert_type": random.choice(ALERT_TYPES),
            "title": title,
            "body": body,
            "is_read": random.choice([True, False]),
        })
    return alerts


def generate_conversations(count, user_id):
    """Generate synthetic conversation sessions."""
    sessions_data = []
    session_titles = [
        "Candidate Sourcing", "Pipeline Review", "Preference Update",
        "Interview Scheduling", "Offer Management", "Skills Assessment",
        "Market Research", "Diversity Hiring", "Compensation Analysis",
        "Onboarding Planning", "Team Restructuring", "Role Definition",
        "Candidate Screening", "Technical Interview Prep", "Reference Checks",
        "Background Verification", "Relocation Assistance", "Visa Sponsorship",
        "Contract Negotiation", "Exit Interview",
    ]
    user_messages = [
        "Find me {title} in {location}",
        "How's the pipeline looking for {title}?",
        "I want candidates with {skill} experience and notice period under {notice_days} days",
        "Rank the top {count} candidates for {title}",
        "Send outreach to {name}",
        "Schedule an interview with {name} for {title}",
        "What's the market rate for {title} in {location}?",
        "Show me candidates with {skill} and {skill2}",
        "I need {count} more candidates for {title}",
        "Update my preferences: prefer {skill} over {skill2}",
    ]
    agent_responses = [
        "I found {count} {title} in the {location} area. {name} ({score}% match) and {name2} ({score2}% match) look strong.",
        "The pipeline for {title} has {count} candidates. {name} ({score}%) and {name2} ({score2}%). The pipeline is thin — I recommend expanding the search.",
        "Updated your preferences: {skill} experience required, notice period ≤ {notice_days} days. This will affect future candidate matching.",
        "Here are the top {count} candidates for {title}: 1) {name} ({score}%), 2) {name2} ({score2}%), 3) {name3} ({score3}%).",
        "Sent outreach message to {name} for the {title} role at {company}. Status: sent.",
        "Interview scheduled with {name} for {title} on 2026-07-{day}. Calendar invite sent.",
        "Market rate for {title} in {location}: ${min_val} - ${max_val}/year. Median: ${median}/year.",
        "Found {count} candidates with {skill} and {skill2}. {name} ({score}%) is the best match.",
        "I've added {count} new candidates matching {title} criteria. Review in the Pipeline tab.",
        "Preferences updated. {skill} weight increased to {weight}, {skill2} weight decreased to {weight2}.",
    ]

    for i in range(count):
        title = random.choice(session_titles)
        num_messages = random.randint(2, 6)
        messages = []
        for j in range(num_messages):
            if j % 2 == 0:
                user_msg = random.choice(user_messages).format(
                    title=random.choice(JOB_TITLES),
                    location=random.choice(LOCATIONS),
                    skill=random.choice([s[0] for s in SKILLS_POOL]),
                    skill2=random.choice([s[0] for s in SKILLS_POOL]),
                    notice_days=random.choice([14, 21, 30]),
                    count=random.randint(5, 20),
                    name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                )
                messages.append({"role": "user", "content": user_msg})
            else:
                agent_msg = random.choice(agent_responses).format(
                    count=random.randint(3, 50),
                    title=random.choice(JOB_TITLES),
                    location=random.choice(LOCATIONS),
                    name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    name2=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    name3=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                    score=random.randint(60, 98),
                    score2=random.randint(50, 85),
                    score3=random.randint(40, 75),
                    company=random.choice(COMPANIES),
                    day=random.randint(20, 28),
                    notice_days=random.choice([14, 21, 30]),
                    min_val=random.randint(120000, 180000),
                    max_val=random.randint(200000, 300000),
                    median=random.randint(150000, 240000),
                    skill=random.choice([s[0] for s in SKILLS_POOL]),
                    skill2=random.choice([s[0] for s in SKILLS_POOL]),
                    weight=round(random.uniform(0.5, 1.0), 2),
                    weight2=round(random.uniform(0.1, 0.5), 2),
                )
                messages.append({
                    "role": "agent",
                    "content": agent_msg,
                    "confidence": round(random.uniform(0.7, 0.99), 2),
                })

        sessions_data.append({"title": title, "messages": messages})
    return sessions_data


async def seed_large_dataset():
    """Generate and insert large synthetic dataset."""
    random.seed(42)  # Reproducible

    async with async_session_factory() as session:
        # Get the recruiter user
        result = await session.execute(select(User).where(User.role == "recruiter"))
        user = result.scalar_one()
        user_id = user.id
        print(f"Using recruiter: {user.email} (id={user_id})")

        # Get/create a session for actions
        result = await session.execute(
            select(AgentConversationSession).where(
                AgentConversationSession.recruiter_id == user_id
            ).order_by(AgentConversationSession.created_at.desc()).limit(1)
        )
        session_obj = result.scalar_one_or_none()
        if not session_obj:
            session_obj = AgentConversationSession(recruiter_id=user_id, title="Large Dataset Session")
            session.add(session_obj)
            await session.flush()
        session_id = session_obj.id

        # ── Generate Candidates ────────────────────────────────────
        existing_emails = set()
        result = await session.execute(select(Candidate.email))
        for row in result.scalars():
            existing_emails.add(row)

        new_candidates = generate_candidates(50)
        added = 0
        for c_data in new_candidates:
            if c_data["email"] not in existing_emails:
                candidate = Candidate(
                    organization_id=uuid.UUID("55757e5e-97eb-4b08-9210-2a18824de387"),
                    owner_id=user_id,
                    **{k: v for k, v in c_data.items() if k != "skills"},
                )
                session.add(candidate)
                await session.flush()

                for skill_data in c_data["skills"]:
                    skill = CandidateSkill(
                        organization_id=uuid.UUID("55757e5e-97eb-4b08-9210-2a18824de387"),
                        candidate_id=candidate.id,
                        **skill_data,
                    )
                    session.add(skill)

                existing_emails.add(c_data["email"])
                added += 1

        print(f"Created {added} new candidates")

        # ── Generate Agent Actions ─────────────────────────────────
        actions = generate_agent_actions(50, user_id, session_id)
        for a_data in actions:
            action = AgentAction(**a_data)
            session.add(action)
        print(f"Created {len(actions)} agent actions")

        # ── Generate Alerts ────────────────────────────────────────
        alerts = generate_alerts(30, user_id)
        for a_data in alerts:
            alert = AgentProactiveAlert(
                recruiter_id=user_id,
                **a_data,
            )
            session.add(alert)
        print(f"Created {len(alerts)} proactive alerts")

        # ── Generate Conversations ─────────────────────────────────
        sessions_data = generate_conversations(10, user_id)
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
                    created_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 168)),
                )
                session.add(msg)
        print(f"Created {len(sessions_data)} conversation sessions")

        await session.commit()
        print("\n✅ Large dataset seed complete!")


if __name__ == "__main__":
    asyncio.run(seed_large_dataset())
