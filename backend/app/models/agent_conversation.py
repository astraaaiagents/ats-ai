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


class AgentConversationSession(Base):
    __tablename__ = "agent_conversation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recruiter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recruiter = relationship("User", back_populates="conversation_sessions")
    messages: Mapped[list["AgentConversationMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="AgentConversationMessage.created_at"
    )
    actions: Mapped[list["AgentAction"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_agent_sessions_recruiter",
            "recruiter_id",
            "created_at",
        ),
    )


class AgentConversationMessage(Base):
    __tablename__ = "agent_conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cards: Mapped[dict | None] = mapped_column(JSON_VARIANT, nullable=True)
    actions: Mapped[dict | None] = mapped_column(JSON_VARIANT, nullable=True)
    sources: Mapped[dict | None] = mapped_column(JSON_VARIANT, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    is_proactive: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session = relationship("AgentConversationSession", back_populates="messages")

    __table_args__ = (
        Index(
            "ix_agent_messages_session",
            "session_id",
            "created_at",
        ),
        Index(
            "ix_agent_messages_role",
            "role",
        ),
    )
