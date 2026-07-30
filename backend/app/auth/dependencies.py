import uuid
from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.middleware.error_handler import AppException
from app.models.user import User

from .jwt import is_token_blacklisted, verify_token
from .password import hash_password

security = HTTPBearer()

# Dev user returned when auth is bypassed
_DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_DEV_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_DEV_USER_EMAIL = "dev@localhost"


async def ensure_dev_user(db: AsyncSession) -> User:
    """Ensure the dev user exists in the database when auth is bypassed.

    When bypass_auth is enabled, get_current_user() returns the dev user.
    This function guarantees that user exists in the DB so that
    FK-constrained inserts (e.g. recruiter_preferences, agent_conversation_sessions)
    do not fail with ForeignKeyViolationError.
    """
    try:
        from app.models.organization import Organization
        org_result = await db.execute(select(Organization).where(Organization.id == _DEV_ORG_ID))
        dev_org = org_result.scalar_one_or_none()
        if not dev_org:
            dev_org = Organization(
                id=_DEV_ORG_ID,
                name="Default Organization",
                slug="default-org",
                is_active=True,
            )
            db.add(dev_org)
            await db.flush()
        default_org_id = _DEV_ORG_ID

        result = await db.execute(
            select(User).where(User.id == _DEV_USER_ID)
        )
        user = result.scalar_one_or_none()
        if user:
            if user.organization_id != default_org_id:
                user.organization_id = default_org_id
                await db.commit()
                await db.refresh(user)
            return user

        user = User(
            id=_DEV_USER_ID,
            email=_DEV_USER_EMAIL,
            password_hash=hash_password("dev"),
            role="recruiter",
            organization_id=default_org_id,
            is_active=True,
            token_version=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception:
        try:
            await db.rollback()
        except Exception:
            pass
        # Retry select in case of concurrent insert
        try:
            result = await db.execute(select(User).where(User.id == _DEV_USER_ID))
            user = result.scalar_one_or_none()
            if user:
                return user
        except Exception:
            pass
        return _make_dev_user_mock()


async def ensure_seed_candidates(db: AsyncSession) -> None:
    """Ensure mock candidates are populated in the database if empty."""
    try:
        from app.models.candidate import Candidate
        from app.models.candidate_skill import CandidateSkill
        from app.models.organization import Organization

        # Check if organization exists
        org_result = await db.execute(select(Organization).where(Organization.id == _DEV_ORG_ID))
        if not org_result.scalar_one_or_none():
            dev_org = Organization(
                id=_DEV_ORG_ID,
                name="Default Organization",
                slug="default-org",
                is_active=True,
            )
            db.add(dev_org)
            await db.flush()

        # Check candidate count
        cand_result = await db.execute(select(Candidate).where(Candidate.organization_id == _DEV_ORG_ID))
        existing_cands = cand_result.scalars().all()
        if len(existing_cands) >= 5:
            return

        mock_data = [
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000101"),
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
                "skills": [("Python", 5, 5.0), ("FastAPI", 4, 3.0), ("PostgreSQL", 4, 4.0), ("Docker", 3, 3.0), ("AWS", 4, 4.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000102"),
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
                "skills": [("Python", 4, 3.0), ("React", 4, 4.0), ("TypeScript", 3, 3.0), ("AWS", 3, 2.0), ("Node.js", 3, 3.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000103"),
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
                "skills": [("Java", 5, 8.0), ("Spring Boot", 5, 6.0), ("AWS", 4, 5.0), ("Microservices", 5, 6.0), ("Kafka", 4, 4.0), ("Kubernetes", 3, 3.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000104"),
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
                "skills": [("Java", 5, 10.0), ("Spring Boot", 5, 8.0), ("AWS", 5, 6.0), ("System Design", 5, 7.0), ("PostgreSQL", 4, 8.0), ("Docker", 4, 5.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000105"),
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
                "skills": [("React", 5, 7.0), ("TypeScript", 5, 6.0), ("Next.js", 4, 4.0), ("GraphQL", 4, 3.0), ("Tailwind CSS", 4, 3.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000106"),
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
                "skills": [("Kubernetes", 5, 5.0), ("Terraform", 4, 4.0), ("AWS", 5, 6.0), ("Python", 4, 4.0), ("CI/CD", 5, 5.0), ("Go", 3, 3.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000107"),
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
                "skills": [("Python", 5, 6.0), ("Spark", 4, 4.0), ("AWS", 4, 5.0), ("SQL", 5, 7.0), ("Airflow", 3, 3.0), ("Snowflake", 3, 3.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000108"),
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
                "skills": [("Java", 5, 6.0), ("Spring Boot", 5, 5.0), ("Microservices", 4, 4.0), ("Oracle DB", 4, 5.0), ("REST APIs", 5, 6.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000109"),
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
                "skills": [("React Native", 4, 4.0), ("TypeScript", 4, 4.0), ("Node.js", 4, 5.0), ("Python", 3, 3.0), ("Firebase", 3, 3.0)],
            },
            {
                "id": uuid.UUID("00000000-0000-0000-0000-000000000110"),
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
                "skills": [("Go", 5, 5.0), ("Python", 5, 6.0), ("PostgreSQL", 5, 6.0), ("Redis", 4, 4.0), ("gRPC", 3, 3.0)],
            },
        ]

        existing_ids = {c.id for c in existing_cands}
        for item in mock_data:
            if item["id"] in existing_ids:
                continue
            cand = Candidate(
                id=item["id"],
                organization_id=_DEV_ORG_ID,
                first_name=item["first_name"],
                last_name=item["last_name"],
                email=item["email"],
                phone=item["phone"],
                current_title=item["current_title"],
                current_employer=item["current_employer"],
                location=item["location"],
                salary_expectation_min=item["salary_expectation_min"],
                salary_expectation_max=item["salary_expectation_max"],
                visa_status=item["visa_status"],
                notice_period_days=item["notice_period_days"],
                source=item["source"],
                status=item["status"],
                ai_summary=item["ai_summary"],
            )
            db.add(cand)
            await db.flush()

            for s_name, prof, yoe in item["skills"]:
                sk = CandidateSkill(
                    id=uuid.uuid4(),
                    organization_id=_DEV_ORG_ID,
                    candidate_id=cand.id,
                    skill_name=s_name,
                    proficiency=prof,
                    years_experience=yoe,
                )
                db.add(sk)

        await db.commit()
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        print(f"Candidate seeding notice: {e}")


def _make_dev_user_mock() -> User:
    """Create a mock dev user for fallback when DB is unavailable."""
    return User(
        id=_DEV_USER_ID,
        email=_DEV_USER_EMAIL,
        password_hash="",
        role="recruiter",
        organization_id=_DEV_ORG_ID,
        is_active=True,
        token_version=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session),
) -> User:
    if credentials and credentials.credentials and credentials.credentials != "dev-token":
        payload = verify_token(credentials.credentials, expected_type="access")
        jti = payload.get("jti")
        if jti:
            blacklisted = await is_token_blacklisted(jti, db)
            if blacklisted:
                raise AppException(
                    code="TOKEN_REVOKED",
                    message="Token has been revoked",
                    status_code=401,
                )

        user_id = payload.get("sub")
        if not user_id:
            raise AppException(
                code="UNAUTHORIZED",
                message="Invalid token payload",
                status_code=401,
            )

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise AppException(
                code="UNAUTHORIZED",
                message="User not found or inactive",
                status_code=401,
            )

        if payload.get("token_version", 0) != user.token_version:
            raise AppException(
                code="TOKEN_REVOKED",
                message="Token has been invalidated",
                status_code=401,
            )

        return user

    # Fallback to dev user when auth is bypassed or dev-token is provided
    if settings.bypass_auth or (credentials and credentials.credentials == "dev-token"):
        return await ensure_dev_user(db)

    raise AppException(
        code="UNAUTHORIZED",
        message="Authentication required",
        status_code=401,
    )


def require_role(roles: list[str]):
    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppException(
                code="FORBIDDEN",
                message="Insufficient permissions",
                status_code=403,
            )
        return current_user

    return _role_checker


async def get_org_id(request: Request) -> str | None:
    return getattr(request.state, "organization_id", None)
