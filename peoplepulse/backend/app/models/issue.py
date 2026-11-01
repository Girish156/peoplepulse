"""Issue SQLAlchemy model (anomaly / data quality issues)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON

from app.db.base import Base
from app.models.base import TimestampMixin


class Issue(Base, TimestampMixin):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    issue_type: Mapped[str] = mapped_column(
        Enum(
            "goal_owner_mismatch",
            "progress_exceeds_scale",
            "reviewer_no_relationship",
            "closed_cycle_edit",
            "untraceable_feedback",
            "other",
            name="issue_type_enum",
        ),
        nullable=False, index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", "critical", name="issue_severity_enum"),
        default="medium", nullable=False, index=True,
    )
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
    )
    resolution_status: Mapped[str] = mapped_column(
        Enum("open", "investigating", "resolved", "dismissed", name="resolution_status_enum"),
        default="open", nullable=False, index=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    evidence_refs: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    resolver: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[resolved_by])
