"""Add skill embeddings for vector search.

Add pgvector support to candidate_skills table:
- skill_embedding vector(1536) column for OpenAI text-embedding-3-small
- HNSW index for efficient cosine similarity search

Revision ID: 006_skill_embeddings
Revises: 005_agent_portal
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "006_skill_embeddings"
down_revision = "005_agent_portal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column to candidate_skills
    op.add_column(
        "candidate_skills",
        sa.Column(
            "skill_embedding",
            Vector(1536),  # 1536 dimensions matches OpenAI text-embedding-3-small
            nullable=True,
        ),
    )

    # Create HNSW index for cosine similarity
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_candidate_skills_skill_embedding "
        "ON candidate_skills USING hnsw (skill_embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 256)"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_candidate_skills_skill_embedding",
        table_name="candidate_skills",
        postgresql_concurrently=True,
    )
    op.drop_column("candidate_skills", "skill_embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
