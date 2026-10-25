import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    venue: Mapped[str] = mapped_column(String(500), nullable=True)
    doi: Mapped[str] = mapped_column(String(500), nullable=True, index=True)
    abstract: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="upload")  # upload, semantic_scholar, openalex
    pdf_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, done, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Extraction fields (populated by UnderstandingAgent)
    research_question: Mapped[str] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(Text, nullable=True)
    methodology: Mapped[str] = mapped_column(Text, nullable=True)
    dataset: Mapped[str] = mapped_column(Text, nullable=True)
    population: Mapped[str] = mapped_column(Text, nullable=True)
    experimental_setup: Mapped[str] = mapped_column(Text, nullable=True)
    baselines: Mapped[str] = mapped_column(Text, nullable=True)
    evaluation_metrics: Mapped[str] = mapped_column(Text, nullable=True)
    results_summary: Mapped[str] = mapped_column(Text, nullable=True)
    contributions: Mapped[str] = mapped_column(Text, nullable=True)
    assumptions: Mapped[str] = mapped_column(Text, nullable=True)
    limitations_text: Mapped[str] = mapped_column(Text, nullable=True)
    future_work: Mapped[str] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="papers")
    sections = relationship("DocumentSection", back_populates="paper", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="paper", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="paper", cascade="all, delete-orphan")
    evidence_spans = relationship("EvidenceSpan", back_populates="paper", cascade="all, delete-orphan")
    limitations = relationship("Limitation", back_populates="paper", cascade="all, delete-orphan")
