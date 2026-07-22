from typing import Any
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, CheckConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CandidateTimeline(Base):
    __tablename__ = "candidate_timeline"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="timeline")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('status_changed', 'skill_added', 'skill_removed', "
            "'document_uploaded', 'note_added', 'contact_made', 'email_sent', "
            "'call_scheduled', 'interview_scheduled', 'interview_completed', "
            "'offer_extended', 'offer_accepted', 'offer_rejected', "
            "'placed', 'rejected', 'archived', 'recycled')",
            name="ck_candidate_timeline_event_type",
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
