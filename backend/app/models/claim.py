import uuid
from sqlalchemy import String, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(100), nullable=True)  # finding, conclusion, hypothesis
    strength: Mapped[str] = mapped_column(String(50), nullable=True)  # strong, moderate, weak
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    page: Mapped[int] = mapped_column(Integer, nullable=True)
    section: Mapped[str] = mapped_column(String(200), nullable=True)

    paper = relationship("Paper", back_populates="claims")
    project = relationship("Project", back_populates="claims")
    evidence_spans = relationship("EvidenceSpan", back_populates="claim", cascade="all, delete-orphan")
