import uuid
from sqlalchemy import String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ResearchGap(Base):
    __tablename__ = "research_gaps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    gap_type: Mapped[str] = mapped_column(String(100), nullable=True)
    # untested_method, missing_population, missing_dataset, conflicting_findings,
    # underexplored_combination, outdated_evaluation, unresolved_limitation
    evidence_paper_ids: Mapped[list] = mapped_column(JSON, nullable=True)
    counter_evidence: Mapped[list] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(50), default="candidate")  # candidate, validated, rejected
    novelty: Mapped[float] = mapped_column(Float, nullable=True)
    importance: Mapped[float] = mapped_column(Float, nullable=True)
    feasibility: Mapped[float] = mapped_column(Float, nullable=True)
    evidence_strength: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    project = relationship("Project", back_populates="research_gaps")
    opportunities = relationship("ResearchOpportunity", back_populates="gap", cascade="all, delete-orphan")
