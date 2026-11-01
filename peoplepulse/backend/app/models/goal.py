"""Goal and GoalVersion SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.db.base import Base
from app.models.base import TimestampMixin


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(String(36), ForeignKey("review_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "completed", "cancelled", name="goal_status_enum"),
        default="draft", nullable=False, index=True,
    )
    weight: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="goals", foreign_keys=[employee_id])
    cycle: Mapped["ReviewCycle"] = relationship("ReviewCycle", back_populates="goals")
    key_results: Mapped[List["KeyResult"]] = relationship("KeyResult", back_populates="goal", cascade="all, delete-orphan")
    check_ins: Mapped[List["CheckIn"]] = relationship("CheckIn", back_populates="goal")
    versions: Mapped[List["GoalVersion"]] = relationship("GoalVersion", back_populates="goal", cascade="all, delete-orphan")


class GoalVersion(Base):
    __tablename__ = "goal_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    goal: Mapped["Goal"] = relationship("Goal", back_populates="versions")
    changer: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[changed_by])
