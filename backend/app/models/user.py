from typing import Any
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
        # soft-delete re-use requires UNIQUE only for active users via partial index
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="recruiter"
    )
    # super_admin has no organization_id; regular users must have one
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization | None"] = relationship(back_populates="users")
    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="owner", foreign_keys="[Candidate.owner_id]"
    )

    __table_args__ = (
        Index(
            "ix_users_active_email",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("role", "recruiter")
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("token_version", 0)
        super().__init__(**kwargs)
