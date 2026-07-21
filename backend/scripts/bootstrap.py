"""Bootstrap script that creates the first SuperAdmin user and default organization.

Connects to the database and:
  1. Creates "Default Organization" if none exist.
  2. Creates a super_admin user with a generated password if none exist.

Run after migrations:
    python -m backend.scripts.bootstrap
"""

import asyncio
import logging
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.auth.password import hash_password

logger = logging.getLogger(__name__)


async def bootstrap() -> None:
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        result = await session.execute(text("SELECT id FROM organizations LIMIT 1"))
        org = result.scalar_one_or_none()

        if org is None:
            org_id = uuid.uuid4()
            slug = f"default-{org_id.hex[:8]}"
            now = datetime.now(tz=timezone.utc)
            await session.execute(
                text(
                    "INSERT INTO organizations (id, name, slug, settings, is_active, created_at, updated_at) "
                    "VALUES (:id, :name, :slug, '{}'::jsonb, true, :now, :now)"
                ),
                {"id": org_id, "name": "Default Organization", "slug": slug, "now": now},
            )
            logger.info("Created default organization (id=%s)", org_id)
        else:
            org_id = org
            logger.info("Organization already exists (id=%s)", org_id)

        result = await session.execute(
            text("SELECT id FROM users WHERE role = 'super_admin' LIMIT 1")
        )
        admin = result.scalar_one_or_none()

        if admin is None:
            password = secrets.token_urlsafe(24)
            password_hash_value = hash_password(password)
            admin_id = uuid.uuid4()
            now = datetime.now(tz=timezone.utc)
            email = f"admin@{('default-' + org_id.hex[:8] if org is None else 'org')}.ats"
            await session.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, role, organization_id, is_active, token_version, created_at, updated_at) "
                    "VALUES (:id, :email, :password_hash, 'super_admin', :org_id, true, 0, :now, :now)"
                ),
                {
                    "id": admin_id,
                    "email": email,
                    "password_hash": password_hash_value,
                    "org_id": org_id,
                    "now": now,
                },
            )
            logger.info("Created super_admin user (email=%s)", email)
            print(f"SuperAdmin created — email: {email}  password: {password}")
        else:
            logger.info("Super admin already exists (id=%s)", admin)

        await session.commit()

    await engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()
