"""add client contact enrichment fields

Revision ID: 007
Revises: 006
Create Date: 2026-07-29

Adds organization_name, title, location, description, status
columns to client_contacts for the Jobs tab.
"""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_contacts", sa.Column("organization_name", sa.String(255), nullable=True))
    op.add_column("client_contacts", sa.Column("title", sa.String(255), nullable=True))
    op.add_column("client_contacts", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("client_contacts", sa.Column("description", sa.String(2000), nullable=True))
    op.add_column("client_contacts", sa.Column("status", sa.String(50), nullable=True, server_default="active"))


def downgrade() -> None:
    op.drop_column("client_contacts", "status")
    op.drop_column("client_contacts", "description")
    op.drop_column("client_contacts", "location")
    op.drop_column("client_contacts", "title")
    op.drop_column("client_contacts", "organization_name")
