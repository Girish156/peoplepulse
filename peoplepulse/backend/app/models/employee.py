"""Employee SQLAlchemy model."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employee_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    employment_status: Mapped[str] = mapped_column(
        Enum("active", "on_leave", "terminated", "contractor", name="employment_status_enum"),
        default="active",
        nullable=False,
    )
    manager_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    termination_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Self-referential relationship
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", remote_side="Employee.id", back_populates="direct_reports", foreign_keys=[manager_id]
    )
    direct_reports: Mapped[List["Employee"]] = relationship(
        "Employee", back_populates="manager", foreign_keys=[manager_id]
    )

    # Other relationships
    goals: Mapped[List["Goal"]] = relationship("Goal", back_populates="employee", foreign_keys="Goal.employee_id")
    check_ins: Mapped[List["CheckIn"]] = relationship("CheckIn", back_populates="employee", foreign_keys="CheckIn.employee_id")
    reviews_as_subject: Mapped[List["Review"]] = relationship("Review", back_populates="employee", foreign_keys="Review.employee_id")
    reviews_as_reviewer: Mapped[List["Review"]] = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    feedback_received: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="subject_employee", foreign_keys="Feedback.subject_employee_id")
    feedback_given: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="author_employee", foreign_keys="Feedback.author_employee_id")
    development_plans: Mapped[List["DevelopmentPlan"]] = relationship("DevelopmentPlan", back_populates="employee", foreign_keys="DevelopmentPlan.employee_id")
