"""Add client_contacts, audit_logs, platform_users; add kms_key_id to organizations.

Revision ID: 003_org_user_models
Revises: 002_rls_policies
Create Date: 2026-07-22 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_org_user_models"
down_revision: Union[str, None] = "002_rls_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix ix_users_active_email to include organization_id
    op.drop_index("ix_users_active_email", table_name="users")
    op.create_index(
        "ix_users_active_email",
        "users",
        ["organization_id", "email"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.add_column(
        "organizations",
        sa.Column("kms_key_id", sa.String(255), nullable=True),
    )
    op.create_table(
        "client_contacts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "email", name="uq_org_contact_email"
        ),
    )
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "platform_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.String(50),
            server_default=sa.text("'super_admin'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        op.f("ix_platform_users_email"),
        "platform_users",
        ["email"],
    )


def downgrade() -> None:
    # Restore ix_users_active_email to original columns
    op.drop_index("ix_users_active_email", table_name="users")
    op.create_index(
        "ix_users_active_email",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.drop_index(op.f("ix_platform_users_email"), table_name="platform_users")
    op.drop_table("platform_users")
    op.drop_table("audit_logs")
    op.drop_table("client_contacts")
    op.drop_column("organizations", "kms_key_id")
