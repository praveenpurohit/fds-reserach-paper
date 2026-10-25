import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Limitation(Base):
    __tablename__ = "limitations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    # methodological, dataset, evaluation, generalization, scalability, reproducibility
    page: Mapped[int] = mapped_column(Integer, nullable=True)

    paper = relationship("Paper", back_populates="limitations")
    project = relationship("Project", back_populates="limitations")


class LimitationCluster(Base):
    __tablename__ = "limitation_clusters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    theme: Mapped[str] = mapped_column(String(500), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)
    limitation_ids: Mapped[list] = mapped_column(JSON, nullable=True)

    project = relationship("Project", back_populates="limitation_clusters")
