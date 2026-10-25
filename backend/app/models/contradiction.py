import uuid
from sqlalchemy import String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Contradiction(Base):
    __tablename__ = "contradictions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    claim_a_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"), nullable=True)
    claim_b_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"), nullable=True)
    contradiction_type: Mapped[str] = mapped_column(String(100), nullable=True)
    # true_contradiction, context_dependent, methodological_disagreement, apparent_contradiction
    factors: Mapped[dict] = mapped_column(JSON, nullable=True)  # {"dataset": "...", "metric": "...", ...}
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_strength_a: Mapped[str] = mapped_column(String(50), nullable=True)
    evidence_strength_b: Mapped[str] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    project = relationship("Project", back_populates="contradictions")
    claim_a = relationship("Claim", foreign_keys=[claim_a_id])
    claim_b = relationship("Claim", foreign_keys=[claim_b_id])
