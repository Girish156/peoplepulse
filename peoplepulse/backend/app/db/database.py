"""
SQLAlchemy engine and session factory.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
import app.models  # Ensure all models are loaded

logger = logging.getLogger("peoplepulse")

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif db_url.startswith("postgresql"):
    connect_args = {"connect_timeout": 3}

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    global engine, SessionLocal
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully with {engine.url.drivername}")
    except Exception as e:
        logger.warning(f"Connection to {db_url} failed ({e}). Falling back to local SQLite: sqlite:///./peoplepulse.db")
        sqlite_url = "sqlite:///./peoplepulse.db"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Local SQLite database initialized successfully.")
