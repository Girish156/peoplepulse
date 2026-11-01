"""Feedback SQLAlchemy model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_feedback_rating_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    feedback_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    subject_employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    author_employee_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    review_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(
        Enum("self", "manager", "peer", name="feedback_type_enum"),
        default="peer", nullable=False,
    )
    competency_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "submitted", "acknowledged", name="feedback_status_enum"),
        default="submitted", nullable=False, index=True,
    )

    subject_employee: Mapped["Employee"] = relationship("Employee", back_populates="feedback_received", foreign_keys=[subject_employee_id])
    author_employee: Mapped["Employee"] = relationship("Employee", back_populates="feedback_given", foreign_keys=[author_employee_id])
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="feedback_items")
    competency: Mapped[Optional["Competency"]] = relationship("Competency", back_populates="feedback_items")
    evidence_items: Mapped[List["Evidence"]] = relationship("Evidence", back_populates="feedback", foreign_keys="Evidence.feedback_id")
