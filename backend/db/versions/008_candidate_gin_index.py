"""Candidate GIN index for full-text search.

Revision ID: 008_candidate_gin_index
Revises: 007_client_contact_enrichment
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '008_candidate_gin_index'
down_revision: Union[str, None] = '007_client_contact_enrichment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create GIN index on candidate names and current_title using to_tsvector
    op.execute(
        """
        CREATE INDEX ix_candidates_fts_search 
        ON candidates USING GIN (
            to_tsvector('english', 
                coalesce(first_name, '') || ' ' || 
                coalesce(last_name, '') || ' ' || 
                coalesce(current_title, '')
            )
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_candidates_fts_search;")
