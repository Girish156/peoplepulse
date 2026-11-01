"""Review and ReviewParticipant SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    cycle_id: Mapped[str] = mapped_column(String(36), ForeignKey("review_cycles.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "in_progress", "submitted", "approved", "archived", name="review_status_enum"),
        default="pending", nullable=False, index=True,
    )
    goal_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    feedback_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="reviews_as_subject", foreign_keys=[employee_id])
    reviewer: Mapped["Employee"] = relationship("Employee", back_populates="reviews_as_reviewer", foreign_keys=[reviewer_id])
    cycle: Mapped["ReviewCycle"] = relationship("ReviewCycle", back_populates="reviews")
    participants: Mapped[List["ReviewParticipant"]] = relationship("ReviewParticipant", back_populates="review", cascade="all, delete-orphan")
    feedback_items: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="review")
    development_plans: Mapped[List["DevelopmentPlan"]] = relationship("DevelopmentPlan", back_populates="review")


class ReviewParticipant(Base):
    __tablename__ = "review_participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id: Mapped[str] = mapped_column(String(36), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("self", "manager", "peer", name="participant_role_enum"),
        default="peer", nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc), nullable=False
    )

    review: Mapped["Review"] = relationship("Review", back_populates="participants")
    participant: Mapped["Employee"] = relationship("Employee", foreign_keys=[participant_employee_id])
