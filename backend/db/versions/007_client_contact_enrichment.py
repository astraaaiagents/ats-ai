"""add client contact enrichment fields

Revision ID: 007
Revises: 006
Create Date: 2026-07-29

Adds organization_name, title, location, description, status
columns to client_contacts for the Jobs tab.
"""

from alembic import op
import sqlalchemy as sa

revision = "007_client_contact_enrichment"
down_revision = "006_skill_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("ALTER TABLE client_contacts ADD COLUMN IF NOT EXISTS organization_name VARCHAR(255)")
        op.execute("ALTER TABLE client_contacts ADD COLUMN IF NOT EXISTS title VARCHAR(255)")
        op.execute("ALTER TABLE client_contacts ADD COLUMN IF NOT EXISTS location VARCHAR(255)")
        op.execute("ALTER TABLE client_contacts ADD COLUMN IF NOT EXISTS description VARCHAR(2000)")
        op.execute("ALTER TABLE client_contacts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active'")
    else:
        # SQLite fallback
        try:
            op.add_column("client_contacts", sa.Column("organization_name", sa.String(255), nullable=True))
        except Exception:
            pass
        try:
            op.add_column("client_contacts", sa.Column("title", sa.String(255), nullable=True))
        except Exception:
            pass
        try:
            op.add_column("client_contacts", sa.Column("location", sa.String(255), nullable=True))
        except Exception:
            pass
        try:
            op.add_column("client_contacts", sa.Column("description", sa.String(2000), nullable=True))
        except Exception:
            pass
        try:
            op.add_column("client_contacts", sa.Column("status", sa.String(50), nullable=True, server_default="active"))
        except Exception:
            pass


def downgrade() -> None:
    op.drop_column("client_contacts", "status")
    op.drop_column("client_contacts", "description")
    op.drop_column("client_contacts", "location")
    op.drop_column("client_contacts", "title")
    op.drop_column("client_contacts", "organization_name")
