import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # query_planner, discovery, expansion, understanding, reasoning, gap, auditor
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, completed, failed
    input_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=True)

    project = relationship("Project", back_populates="agent_runs")
