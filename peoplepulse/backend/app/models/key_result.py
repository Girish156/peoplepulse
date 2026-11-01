"""KeyResult SQLAlchemy model."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class KeyResult(Base, TimestampMixin):
    __tablename__ = "key_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_result_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    goal_id: Mapped[str] = mapped_column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    metric_type: Mapped[str] = mapped_column(
        Enum("percentage", "count", "boolean", "currency", "score", name="metric_type_enum"),
        default="count", nullable=False,
    )
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    baseline: Mapped[float] = mapped_column(Numeric(15, 4), default=0, nullable=False)
    target: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    actual: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    weight: Mapped[float] = mapped_column(Numeric(5, 4), default=1.0, nullable=False)
    allowed_progress_scale: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    goal: Mapped["Goal"] = relationship("Goal", back_populates="key_results")
