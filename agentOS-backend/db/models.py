from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Float, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Task(Base):
    __tablename__ = "tasks"

    id:                    Mapped[str]           = mapped_column(String(36),  primary_key=True)
    description:           Mapped[str]           = mapped_column(Text,        nullable=False)
    status:                Mapped[str]           = mapped_column(String(16),  default="pending")
    human_review:          Mapped[bool]          = mapped_column(Boolean,     default=False)
    human_review_required: Mapped[bool]          = mapped_column(Boolean,     default=False)
    human_approved:        Mapped[bool | None]   = mapped_column(Boolean,     nullable=True)
    human_feedback:        Mapped[str | None]    = mapped_column(String(2000), nullable=True)
    created_at:            Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at:            Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    duration_seconds:      Mapped[float | None]  = mapped_column(Float,       nullable=True)
    final_output:          Mapped[str | None]    = mapped_column(Text,        nullable=True)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id:           Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id:      Mapped[str]          = mapped_column(String(36), ForeignKey("tasks.id"), index=True)
    agent_name:   Mapped[str]          = mapped_column(String(32))   # Planner/Research/Executor/Critic/Memory
    status:       Mapped[str]          = mapped_column(String(16), default="pending")
    input_text:   Mapped[str | None]   = mapped_column(Text, nullable=True)
    output_text:  Mapped[str | None]   = mapped_column(Text, nullable=True)
    started_at:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
