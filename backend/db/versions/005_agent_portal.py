"""Add agent portal tables.

Add recruiter_preferences, agent_conversation_sessions, agent_conversation_messages,
agent_actions, agent_proactive_alerts, and preference_learning_events tables.
Add pgvector extension for skill embeddings and implicit preference vectors.

Revision ID: 005_agent_portal
Revises: 004_candidate_models
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "005_agent_portal"
down_revision: Union[str, None] = "004_candidate_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension for vector similarity search
    # 1536 dimensions matches OpenAI text-embedding-3-small
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- recruiter_preferences ---
    # Stores recruiter candidate-matching preferences (explicit JSONB rules +
    # implicit pgvector embeddings learned from recruiter actions).
    op.create_table(
        "recruiter_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "explicit_preferences",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # Implicit preference vector: 1536 dimensions (OpenAI text-embedding-3-small)
        # Dimensions represent learned preference weights (e.g., cloud_experience: 0.85,
        # leadership_experience: 0.72, startup_experience: 0.30).
        sa.Column(
            "implicit_preference_vector",
            Vector(1536),  # 1536 dimensions matches OpenAI text-embedding-3-small
            nullable=True,
        ),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recruiter_id", name="uq_recruiter_preferences_recruiter_id"),
    )
    op.create_index(
        op.f("ix_recruiter_preferences_recruiter_id"),
        "recruiter_preferences",
        ["recruiter_id"],
    )
    # HNSW index for vector similarity search on implicit preferences
    op.execute(
        "CREATE INDEX ix_recruiter_preferences_implicit_vector "
        "ON recruiter_preferences "
        "USING hnsw (implicit_preference_vector vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 256)"
    )

    # --- agent_conversation_sessions ---
    # Conversation sessions for each recruiter. Auto-pruned after 90 days
    # via scheduled task (not enforced at DB level to allow GDPR export first).
    op.create_table(
        "agent_conversation_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=True),
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
        op.f("ix_agent_sessions_recruiter"),
        "agent_conversation_sessions",
        ["recruiter_id", "created_at"],
    )

    # --- agent_conversation_messages ---
    # Messages within a conversation session. Cards, actions, and sources are
    # stored as JSONB for flexible structured content.
    op.create_table(
        "agent_conversation_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_conversation_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("cards", postgresql.JSONB, nullable=True),
        sa.Column("actions", postgresql.JSONB, nullable=True),
        sa.Column("sources", postgresql.JSONB, nullable=True),
        sa.Column(
            "confidence",
            sa.Numeric(3, 2),
            nullable=True,
        ),
        sa.Column(
            "is_proactive",
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_messages_session"),
        "agent_conversation_messages",
        ["session_id", "created_at"],
    )
    op.create_index(
        op.f("ix_agent_messages_role"),
        "agent_conversation_messages",
        ["role"],
    )

    # --- agent_actions (EU AI Act audit log) ---
    # Every agent tool call, decision, and data access is logged here.
    # input_pseudonymized and output_pseudonymized contain SHA-256 hashed
    # identifiers (candidate names, emails, phone numbers replaced with
    # sha256(original_value)) to comply with GDPR while maintaining audit trail.
    op.create_table(
        "agent_actions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_conversation_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("input_pseudonymized", sa.Text, nullable=False),
        sa.Column("output_pseudonymized", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_check_constraint(
        "ck_agent_actions_action_type",
        "agent_actions",
        "action_type IN ('source', 'rank', 'outreach', 'preference_update', "
        "'proactive_alert', 'intent_parse')",
    )
    op.create_check_constraint(
        "ck_agent_actions_agent_name",
        "agent_actions",
        "agent_name IN ('orchestrator', 'sourcing', 'ranking', 'outreach', 'preference_engine')",
    )
    op.create_index(
        op.f("ix_agent_actions_recruiter"),
        "agent_actions",
        ["recruiter_id", "created_at"],
    )
    op.create_index(
        op.f("ix_agent_actions_type"),
        "agent_actions",
        ["action_type", "created_at"],
    )

    # --- agent_proactive_alerts ---
    # Agent-initiated notifications pushed to recruiter via SSE.
    op.create_table(
        "agent_proactive_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=True),
        sa.Column(
            "is_read",
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_check_constraint(
        "ck_agent_alerts_alert_type",
        "agent_proactive_alerts",
        "alert_type IN ('new_match', 'pipeline_update', 'feedback_reminder', 'weekly_digest')",
    )
    op.create_index(
        op.f("ix_agent_alerts_recruiter"),
        "agent_proactive_alerts",
        ["recruiter_id", "is_read", "created_at"],
    )

    # --- preference_learning_events ---
    # Tracks how recruiter preferences evolved over time. Used for transparency,
    # debugging, and GDPR "right to rectification".
    op.create_table(
        "preference_learning_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("features_before", postgresql.JSONB, nullable=True),
        sa.Column("features_after", postgresql.JSONB, nullable=True),
        sa.Column("preference_delta", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_check_constraint(
        "ck_preference_events_event_type",
        "preference_learning_events",
        "event_type IN ('approval', 'rejection', 'explicit_statement', "
        "'outreach_edit', 'outreach_response')",
    )
    op.create_index(
        op.f("ix_preference_events_recruiter"),
        "preference_learning_events",
        ["recruiter_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("preference_learning_events")
    op.drop_table("agent_proactive_alerts")
    op.drop_table("agent_actions")
    op.drop_table("agent_conversation_messages")
    op.drop_table("agent_conversation_sessions")
    op.drop_table("recruiter_preferences")
    op.execute("DROP EXTENSION IF EXISTS vector")
