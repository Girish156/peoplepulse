"""ReviewCycle SQLAlchemy model."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import Date, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class ReviewCycle(Base, TimestampMixin):
    __tablename__ = "review_cycles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    cycle_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("draft", "active", "closed", "archived", name="cycle_status_enum"),
        default="draft",
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    goals: Mapped[List["Goal"]] = relationship("Goal", back_populates="cycle")
    check_ins: Mapped[List["CheckIn"]] = relationship("CheckIn", back_populates="cycle")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="cycle")
