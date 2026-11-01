"""CheckIn and Evidence SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.db.base import Base


class CheckIn(Base):
    __tablename__ = "check_ins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_in_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(String(36), ForeignKey("review_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    check_in_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "submitted", name="check_in_status_enum"),
        default="submitted", nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="check_ins", foreign_keys=[employee_id])
    goal: Mapped["Goal"] = relationship("Goal", back_populates="check_ins")
    cycle: Mapped["ReviewCycle"] = relationship("ReviewCycle", back_populates="check_ins")
    evidence_items: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="check_in", foreign_keys="Evidence.check_in_id")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evidence_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    check_in_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("check_ins.id", ondelete="SET NULL"), nullable=True)
    feedback_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("feedback.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    evidence_type: Mapped[str] = mapped_column(
        Enum("document", "url", "screenshot", "note", "metric", name="evidence_type_enum"),
        default="note", nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    check_in: Mapped[Optional["CheckIn"]] = relationship("CheckIn", back_populates="evidence_items", foreign_keys=[check_in_id])
    feedback: Mapped[Optional["Feedback"]] = relationship("Feedback", back_populates="evidence_items", foreign_keys=[feedback_id])
