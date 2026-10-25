import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)
    heading: Mapped[str] = mapped_column(String(500), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    section_type: Mapped[str] = mapped_column(String(100), nullable=True)  # abstract, introduction, method, results, etc.
    page_start: Mapped[int] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int] = mapped_column(Integer, nullable=True)

    paper = relationship("Paper", back_populates="sections")
    chunks = relationship("DocumentChunk", back_populates="section", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id: Mapped[str] = mapped_column(String, ForeignKey("document_sections.id"), nullable=True)
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)

    section = relationship("DocumentSection", back_populates="chunks")
    paper = relationship("Paper", back_populates="chunks")
