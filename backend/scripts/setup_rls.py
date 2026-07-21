"""Enable Row-Level Security on all tenant-scoped tables.

Connects to the database, enables RLS, and creates tenant isolation policies
using the current_setting('app.organization_id') pattern.

Run after migrations:
    python -m backend.scripts.setup_rls
"""

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

TENANT_POLICIES = [
    {
        "table": "organizations",
        "policy_name": "organizations_tenant_isolation",
        "using": "id = current_setting('app.organization_id')::uuid",
    },
    {
        "table": "users",
        "policy_name": "users_tenant_isolation",
        "using": "organization_id = current_setting('app.organization_id')::uuid",
    },
]


async def setup_rls() -> None:
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession)

    async with async_session() as session:
        for policy in TENANT_POLICIES:
            table = policy["table"]
            policy_name = policy["policy_name"]
            using = policy["using"]

            logger.info("Enabling RLS on %s", table)
            await session.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))

            logger.info("Creating policy %s on %s", policy_name, table)
            await session.execute(
                text(
                    f"CREATE POLICY {policy_name} ON {table} "
                    f"USING ({using})"
                )
            )

        await session.commit()
        logger.info("RLS setup complete")

    await engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(setup_rls())


if __name__ == "__main__":
    main()
