from typing import Any
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    Text,
    Uuid as UUID,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")

# pgvector Vector type — 1536 dimensions for OpenAI text-embedding-3-small
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1536)
except ImportError:
    # Fallback: use JSONB string when pgvector is not installed
    VECTOR_TYPE = Text  # type: ignore[misc,assignment]


class RecruiterPreference(Base):
    __tablename__ = "recruiter_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Explicit preferences: hard rules set by recruiter
    # Example: {"min_experience_years": 5, "required_visa_status": "US_work_authorization",
    #           "preferred_locations": ["NYC", "Remote"], "max_notice_period_days": 30}
    explicit_preferences: Mapped[dict] = mapped_column(
        "explicit_preferences", JSON_VARIANT, nullable=False, default={}
    )
    # Implicit preference vector: 1536 dimensions (OpenAI text-embedding-3-small)
    # Learned from recruiter actions (approvals, rejections, outreach edits)
    implicit_preference_vector: Mapped[Any | None] = mapped_column(VECTOR_TYPE, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recruiter = relationship("User", back_populates="recruiter_preferences")

    __table_args__ = (
        Index(
            "ix_recruiter_preferences_recruiter_id",
            "recruiter_id",
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("explicit_preferences", {})
        super().__init__(**kwargs)
