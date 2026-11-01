"""
Database session dependency for FastAPI endpoints.
"""
from __future__ import annotations

from typing import Generator

from app.db.database import SessionLocal


def get_db() -> Generator:
    """
    Yield a SQLAlchemy session and close it after the request finishes.

    Usage::

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
