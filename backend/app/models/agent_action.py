import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid as UUID,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentAction(Base):
    """EU AI Act compliant audit log for all agent actions.

    input_pseudonymized and output_pseudonymized contain SHA-256 hashed
    identifiers to comply with GDPR while maintaining an audit trail.
    PII fields (names, emails, phone numbers) are replaced with their
    SHA-256 hash before storage.
    """

    __tablename__ = "agent_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    input_pseudonymized: Mapped[str] = mapped_column(Text, nullable=False)
    output_pseudonymized: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recruiter = relationship("User", back_populates="agent_actions")
    session = relationship("AgentConversationSession", back_populates="actions")

    __table_args__ = (
        Index(
            "ix_agent_actions_recruiter",
            "recruiter_id",
            "created_at",
        ),
        Index(
            "ix_agent_actions_type",
            "action_type",
            "created_at",
        ),
    )

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("action_type", "source")
        kwargs.setdefault("agent_name", "orchestrator")
        super().__init__(**kwargs)
