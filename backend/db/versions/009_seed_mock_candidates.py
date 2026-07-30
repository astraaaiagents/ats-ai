"""Seed mock candidates and candidate_skills.

Revision ID: 009_seed_mock_candidates
Revises: 008_candidate_gin_index
Create Date: 2026-07-30
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "009_seed_mock_candidates"
down_revision: Union[str, None] = "008_candidate_gin_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"

MOCK_CANDIDATES = [
    {
        "id": "00000000-0000-0000-0000-000000000101",
        "first_name": "Sarah",
        "last_name": "Connor",
        "email": "sarah.connor@example.com",
        "phone": "+1-555-0101",
        "current_title": "Senior Python Developer",
        "current_employer": "TechCorp",
        "location": "San Francisco, CA",
        "salary_expectation_min": 150000,
        "salary_expectation_max": 180000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "LinkedIn",
        "status": "sourced",
        "ai_summary": "Experienced Python Developer with strong background in FastAPI, PostgreSQL, and AWS microservices.",
        "skills": [
            ("Python", 5, 5.0),
            ("FastAPI", 4, 3.0),
            ("PostgreSQL", 4, 4.0),
            ("Docker", 3, 3.0),
            ("AWS", 4, 4.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000102",
        "first_name": "Alex",
        "last_name": "Mercer",
        "email": "alex.mercer@example.com",
        "phone": "+1-555-0102",
        "current_title": "Full Stack Engineer",
        "current_employer": "DataDrive",
        "location": "New York, NY",
        "salary_expectation_min": 140000,
        "salary_expectation_max": 165000,
        "visa_status": "H1B",
        "notice_period_days": 30,
        "source": "Referral",
        "status": "sourced",
        "ai_summary": "Versatile Full Stack Engineer proficient in Python, React, and AWS cloud architecture.",
        "skills": [
            ("Python", 4, 3.0),
            ("React", 4, 4.0),
            ("TypeScript", 3, 3.0),
            ("AWS", 3, 2.0),
            ("Node.js", 3, 3.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000103",
        "first_name": "Michael",
        "last_name": "Chen",
        "email": "michael.chen@example.com",
        "phone": "+1-555-0103",
        "current_title": "Senior Java Backend Engineer",
        "current_employer": "Enterprise Cloud Solutions",
        "location": "Seattle, WA",
        "salary_expectation_min": 160000,
        "salary_expectation_max": 195000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "LinkedIn",
        "status": "sourced",
        "ai_summary": "Senior Backend Engineer specializing in Java, Spring Boot, distributed microservices, and AWS.",
        "skills": [
            ("Java", 5, 8.0),
            ("Spring Boot", 5, 6.0),
            ("AWS", 4, 5.0),
            ("Microservices", 5, 6.0),
            ("Kafka", 4, 4.0),
            ("Kubernetes", 3, 3.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000104",
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya.sharma@example.com",
        "phone": "+1-555-0104",
        "current_title": "Lead Java & Cloud Architect",
        "current_employer": "FinTech Global",
        "location": "Austin, TX",
        "salary_expectation_min": 175000,
        "salary_expectation_max": 210000,
        "visa_status": "Green Card",
        "notice_period_days": 30,
        "source": "Indeed",
        "status": "sourced",
        "ai_summary": "Lead Architect with 10+ years designing enterprise Java applications and high-throughput AWS infrastructure.",
        "skills": [
            ("Java", 5, 10.0),
            ("Spring Boot", 5, 8.0),
            ("AWS", 5, 6.0),
            ("System Design", 5, 7.0),
            ("PostgreSQL", 4, 8.0),
            ("Docker", 4, 5.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000105",
        "first_name": "David",
        "last_name": "Kim",
        "email": "david.kim@example.com",
        "phone": "+1-555-0105",
        "current_title": "Frontend Lead Engineer",
        "current_employer": "WebScale Inc",
        "location": "San Jose, CA",
        "salary_expectation_min": 160000,
        "salary_expectation_max": 190000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "GitHub",
        "status": "sourced",
        "ai_summary": "Frontend Architect expert in React, TypeScript, Next.js, and web application performance optimization.",
        "skills": [
            ("React", 5, 7.0),
            ("TypeScript", 5, 6.0),
            ("Next.js", 4, 4.0),
            ("GraphQL", 4, 3.0),
            ("Tailwind CSS", 4, 3.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000106",
        "first_name": "Elena",
        "last_name": "Rostova",
        "email": "elena.rostova@example.com",
        "phone": "+1-555-0106",
        "current_title": "DevOps & Site Reliability Engineer",
        "current_employer": "CloudNative Systems",
        "location": "Boston, MA",
        "salary_expectation_min": 155000,
        "salary_expectation_max": 185000,
        "visa_status": "H1B",
        "notice_period_days": 30,
        "source": "LinkedIn",
        "status": "sourced",
        "ai_summary": "SRE & DevOps Engineer skilled in Kubernetes, Terraform, AWS automation, CI/CD pipelines, and Python scripting.",
        "skills": [
            ("Kubernetes", 5, 5.0),
            ("Terraform", 4, 4.0),
            ("AWS", 5, 6.0),
            ("Python", 4, 4.0),
            ("CI/CD", 5, 5.0),
            ("Go", 3, 3.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000107",
        "first_name": "James",
        "last_name": "Wilson",
        "email": "james.wilson@example.com",
        "phone": "+1-555-0107",
        "current_title": "Data Engineer",
        "current_employer": "Analytics Hub",
        "location": "Chicago, IL",
        "salary_expectation_min": 145000,
        "salary_expectation_max": 175000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "Referral",
        "status": "sourced",
        "ai_summary": "Data Engineer specializing in Python, Apache Spark, Snowflake, Airflow, and cloud data warehousing on AWS.",
        "skills": [
            ("Python", 5, 6.0),
            ("Spark", 4, 4.0),
            ("AWS", 4, 5.0),
            ("SQL", 5, 7.0),
            ("Airflow", 3, 3.0),
            ("Snowflake", 3, 3.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000108",
        "first_name": "Anita",
        "last_name": "Patel",
        "email": "anita.patel@example.com",
        "phone": "+1-555-0108",
        "current_title": "Senior Java Developer",
        "current_employer": "HealthTech Labs",
        "location": "Atlanta, GA",
        "salary_expectation_min": 140000,
        "salary_expectation_max": 170000,
        "visa_status": "Green Card",
        "notice_period_days": 14,
        "source": "LinkedIn",
        "status": "sourced",
        "ai_summary": "Java Developer with extensive experience in Spring Boot REST APIs, microservices, and healthcare systems.",
        "skills": [
            ("Java", 5, 6.0),
            ("Spring Boot", 5, 5.0),
            ("Microservices", 4, 4.0),
            ("Oracle DB", 4, 5.0),
            ("REST APIs", 5, 6.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000109",
        "first_name": "Lucas",
        "last_name": "Silva",
        "email": "lucas.silva@example.com",
        "phone": "+1-555-0109",
        "current_title": "Mobile & Full Stack Developer",
        "current_employer": "MobileFirst",
        "location": "Miami, FL",
        "salary_expectation_min": 135000,
        "salary_expectation_max": 160000,
        "visa_status": "TN Visa",
        "notice_period_days": 14,
        "source": "Indeed",
        "status": "sourced",
        "ai_summary": "Full stack and mobile developer skilled in React Native, TypeScript, Node.js, and backend Python services.",
        "skills": [
            ("React Native", 4, 4.0),
            ("TypeScript", 4, 4.0),
            ("Node.js", 4, 5.0),
            ("Python", 3, 3.0),
            ("Firebase", 3, 3.0),
        ],
    },
    {
        "id": "00000000-0000-0000-0000-000000000110",
        "first_name": "Rachel",
        "last_name": "Green",
        "email": "rachel.green@example.com",
        "phone": "+1-555-0110",
        "current_title": "Staff Backend Engineer",
        "current_employer": "SaaS Metrics",
        "location": "Denver, CO",
        "salary_expectation_min": 170000,
        "salary_expectation_max": 205000,
        "visa_status": "US Citizen",
        "notice_period_days": 14,
        "source": "LinkedIn",
        "status": "sourced",
        "ai_summary": "Staff Engineer expert in Go, Python, PostgreSQL, Redis, and high-performance microservice architectures.",
        "skills": [
            ("Go", 5, 5.0),
            ("Python", 5, 6.0),
            ("PostgreSQL", 5, 6.0),
            ("Redis", 4, 4.0),
            ("gRPC", 3, 3.0),
        ],
    },
]


def upgrade() -> None:
    # 1. Ensure default organization exists
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute(
            f"""
            INSERT INTO organizations (id, name, slug, settings, is_active, created_at, updated_at)
            VALUES ('{DEFAULT_ORG_ID}'::uuid, 'Default Organization', 'default-org', '{{}}'::jsonb, true, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING;
            """
        )
    else:
        op.execute(
            f"""
            INSERT OR IGNORE INTO organizations (id, name, slug, settings, is_active)
            VALUES ('{DEFAULT_ORG_ID}', 'Default Organization', 'default-org', '{{}}', 1);
            """
        )

    # 2. Insert mock candidates and skills
    for c in MOCK_CANDIDATES:
        c_id = c["id"]
        first_name = c["first_name"]
        last_name = c["last_name"]
        email = c["email"]
        phone = c["phone"]
        title = c["current_title"]
        employer = c["current_employer"]
        location = c["location"]
        sal_min = c["salary_expectation_min"]
        sal_max = c["salary_expectation_max"]
        visa = c["visa_status"]
        notice = c["notice_period_days"]
        source = c["source"]
        status = c["status"]
        ai_summary = c["ai_summary"].replace("'", "''")

        if is_postgres:
            op.execute(
                f"""
                INSERT INTO candidates (
                    id, organization_id, first_name, last_name, email, phone,
                    current_title, current_employer, location,
                    salary_expectation_min, salary_expectation_max, visa_status,
                    notice_period_days, source, status, ai_summary,
                    created_at, updated_at
                ) VALUES (
                    '{c_id}'::uuid, '{DEFAULT_ORG_ID}'::uuid, '{first_name}', '{last_name}', '{email}', '{phone}',
                    '{title}', '{employer}', '{location}',
                    {sal_min}, {sal_max}, '{visa}',
                    {notice}, '{source}', '{status}', '{ai_summary}',
                    NOW(), NOW()
                ) ON CONFLICT (id) DO NOTHING;
                """
            )
        else:
            op.execute(
                f"""
                INSERT OR IGNORE INTO candidates (
                    id, organization_id, first_name, last_name, email, phone,
                    current_title, current_employer, location,
                    salary_expectation_min, salary_expectation_max, visa_status,
                    notice_period_days, source, status, ai_summary
                ) VALUES (
                    '{c_id}', '{DEFAULT_ORG_ID}', '{first_name}', '{last_name}', '{email}', '{phone}',
                    '{title}', '{employer}', '{location}',
                    {sal_min}, {sal_max}, '{visa}',
                    {notice}, '{source}', '{status}', '{ai_summary}'
                );
                """
            )

        for skill_name, prof, yoe in c["skills"]:
            s_id = str(uuid.uuid4())
            skill_name_escaped = skill_name.replace("'", "''")
            if is_postgres:
                op.execute(
                    f"""
                    INSERT INTO candidate_skills (
                        id, organization_id, candidate_id, skill_name, proficiency, years_experience
                    ) VALUES (
                        '{s_id}'::uuid, '{DEFAULT_ORG_ID}'::uuid, '{c_id}'::uuid, '{skill_name_escaped}', {prof}, {yoe}
                    ) ON CONFLICT (candidate_id, skill_name) DO NOTHING;
                    """
                )
            else:
                op.execute(
                    f"""
                    INSERT OR IGNORE INTO candidate_skills (
                        id, organization_id, candidate_id, skill_name, proficiency, years_experience
                    ) VALUES (
                        '{s_id}', '{DEFAULT_ORG_ID}', '{c_id}', '{skill_name_escaped}', {prof}, {yoe}
                    );
                    """
                )


def downgrade() -> None:
    for c in MOCK_CANDIDATES:
        c_id = c["id"]
        op.execute(f"DELETE FROM candidate_skills WHERE candidate_id = '{c_id}';")
        op.execute(f"DELETE FROM candidates WHERE id = '{c_id}';")
