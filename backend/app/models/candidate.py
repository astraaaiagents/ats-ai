from enum import Enum as PyEnum
from typing import Any
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CandidateSource(str, PyEnum):
    LINKEDIN = "linkedin"
    DRIBBBLE = "dribbble"
    GITHUB = "github"
    REFERRAL = "referral"
    AGENCY_DB = "agency_db"
    MANUAL = "manual"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_employer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_expectation_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_expectation_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visa_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="sourced")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_ai_summary_edited: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    skills: Mapped[list["CandidateSkill"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    documents: Mapped[list["CandidateDocument"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    timeline: Mapped[list["CandidateTimeline"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    owner = relationship("User", back_populates="candidates", foreign_keys=[owner_id])

    __table_args__ = (
        Index(
            "ix_candidates_active_email",
            "organization_id",
            "email",
            unique=True,
            postgresql_where=text("status != 'archived'"),
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("status", "sourced")
        kwargs.setdefault("is_ai_summary_edited", False)
        super().__init__(**kwargs)
