"""Enable Row-Level Security and create tenant isolation policies.

Revision ID: 002_rls_policies
Revises: 001_initial_schema
Create Date: 2026-07-22 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002_rls_policies"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY organizations_tenant_isolation ON organizations "
        "USING (id = current_setting('app.organization_id')::uuid)"
    )
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY users_tenant_isolation ON users "
        "USING (organization_id = current_setting('app.organization_id')::uuid)"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS users_tenant_isolation ON users")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS organizations_tenant_isolation ON organizations")
    op.execute("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY")
