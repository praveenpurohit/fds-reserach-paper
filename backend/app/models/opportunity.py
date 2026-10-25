import uuid
from sqlalchemy import String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ResearchOpportunity(Base):
    __tablename__ = "research_opportunities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    gap_id: Mapped[str] = mapped_column(String, ForeignKey("research_gaps.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=True)
    current_state: Mapped[str] = mapped_column(Text, nullable=True)
    missing_evidence: Mapped[str] = mapped_column(Text, nullable=True)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=True)
    supporting_evidence: Mapped[list] = mapped_column(JSON, nullable=True)
    counter_evidence: Mapped[list] = mapped_column(JSON, nullable=True)
    novelty_score: Mapped[float] = mapped_column(Float, nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, nullable=True)
    feasibility_score: Mapped[float] = mapped_column(Float, nullable=True)
    evidence_strength_score: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    suggested_questions: Mapped[list] = mapped_column(JSON, nullable=True)
    suggested_hypotheses: Mapped[list] = mapped_column(JSON, nullable=True)

    gap = relationship("ResearchGap", back_populates="opportunities")
    project = relationship("Project", back_populates="research_opportunities")
