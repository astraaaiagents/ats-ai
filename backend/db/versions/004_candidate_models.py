"""Add candidate management tables.

Add candidates, candidate_skills, candidate_documents, candidate_timeline tables.

Revision ID: 004_candidate_models
Revises: 003_org_user_models
Create Date: 2026-07-22 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_candidate_models"
down_revision: Union[str, None] = "003_org_user_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create candidates table
    op.create_table(
        "candidates",
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
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("current_title", sa.String(255), nullable=True),
        sa.Column("current_employer", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("salary_expectation_min", sa.Integer, nullable=True),
        sa.Column("salary_expectation_max", sa.Integer, nullable=True),
        sa.Column("visa_status", sa.String(100), nullable=True),
        sa.Column("notice_period_days", sa.Integer, nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="sourced"),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column(
            "ai_summary_generated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_ai_summary_edited",
            sa.Boolean,
            server_default=sa.text("false"),
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
    )
    op.create_index(
        "ix_candidates_active_email",
        "candidates",
        ["organization_id", "email"],
        unique=True,
        postgresql_where=sa.text("status != 'archived'"),
    )
    op.create_index(op.f("ix_candidates_organization_id"), "candidates", ["organization_id"])

    # Create candidate_skills table
    op.create_table(
        "candidate_skills",
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
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("proficiency", sa.Integer, nullable=True),
        sa.Column("years_experience", sa.Float, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "candidate_id", "skill_name", name="uq_candidate_skill_name"
        ),
    )
    op.create_index(
        op.f("ix_candidate_skills_candidate_id"),
        "candidate_skills",
        ["candidate_id"],
    )

    # Create candidate_documents table
    op.create_table(
        "candidate_documents",
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
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_candidate_documents_candidate_id"),
        "candidate_documents",
        ["candidate_id"],
    )

    # Create candidate_timeline table
    op.create_table(
        "candidate_timeline",
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
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_candidate_timeline_candidate_id"),
        "candidate_timeline",
        ["candidate_id"],
    )
    op.create_index(
        op.f("ix_candidate_timeline_organization_id"),
        "candidate_timeline",
        ["organization_id"],
    )
    op.create_check_constraint(
        "ck_candidate_timeline_event_type",
        "candidate_timeline",
        "event_type IN ('status_changed', 'skill_added', 'skill_removed', "
        "'document_uploaded', 'note_added', 'contact_made', 'email_sent', "
        "'call_scheduled', 'interview_scheduled', 'interview_completed', "
        "'offer_extended', 'offer_accepted', 'offer_rejected', "
        "'placed', 'rejected', 'archived', 'recycled')",
    )


def downgrade() -> None:
    op.drop_table("candidate_timeline")
    op.drop_table("candidate_documents")
    op.drop_table("candidate_skills")
    op.drop_table("candidates")
