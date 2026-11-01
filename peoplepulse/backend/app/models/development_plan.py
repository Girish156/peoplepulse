"""DevelopmentPlan and DevelopmentPlanAction SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class DevelopmentPlan(Base, TimestampMixin):
    __tablename__ = "development_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    review_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True)
    objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "completed", "cancelled", name="dev_plan_status_enum"),
        default="draft", nullable=False, index=True,
    )
    approver_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="development_plans", foreign_keys=[employee_id])
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="development_plans")
    approver: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[approver_id])
    actions: Mapped[List["DevelopmentPlanAction"]] = relationship(
        "DevelopmentPlanAction", back_populates="plan", cascade="all, delete-orphan"
    )


class DevelopmentPlanAction(Base, TimestampMixin):
    __tablename__ = "development_plan_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("development_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "completed", "cancelled", name="action_status_enum"),
        default="pending", nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped["DevelopmentPlan"] = relationship("DevelopmentPlan", back_populates="actions")
