import uuid
from sqlalchemy import String, Text, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=True)
    section: Mapped[str] = mapped_column(String(200), nullable=True)
    relationship_type: Mapped[str] = mapped_column(String(50), default="SUPPORTS")  # SUPPORTS, CONTRADICTS, QUALIFIES
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    paper = relationship("Paper", back_populates="evidence_spans")
    claim = relationship("Claim", back_populates="evidence_spans")
