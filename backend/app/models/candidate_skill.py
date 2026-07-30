from typing import Any
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint, Uuid as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# pgvector Vector type — 1536 dimensions for OpenAI text-embedding-3-small
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1536)
except ImportError:
    # Fallback: use Float or Text when pgvector is not installed
    from sqlalchemy import Float
    VECTOR_TYPE = Float  # type: ignore[misc,assignment]

from app.database import Base


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

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
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    skill_embedding: Mapped[Any | None] = mapped_column(VECTOR_TYPE, nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="skills")

    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "skill_name", name="uq_candidate_skill_name"
        ),
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
