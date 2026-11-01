"""
PeoplePulse Reference Data Seeder
=================================
Seeds foundational reference data into PostgreSQL or SQLite:
- Competencies
- Review cycles
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Ensure backend app models can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.models.competency import Competency
from app.models.review_cycle import ReviewCycle
from app.db.base import Base

DEFAULT_COMPETENCIES = [
    ("COMP-001", "Leadership", "Inspiring, motivating, and guiding team members to achieve shared organizational goals.", 5),
    ("COMP-002", "Communication", "Articulating ideas clearly and actively listening to stakeholders across all levels.", 5),
    ("COMP-003", "Technical Expertise", "Demonstrating deep mastery of technical domains, architectures, and engineering best practices.", 5),
    ("COMP-004", "Collaboration", "Partnering effectively across departmental boundaries and fostering psychological safety.", 5),
    ("COMP-005", "Innovation", "Challenging conventional assumptions, generating creative ideas, and driving continuous improvement.", 5),
    ("COMP-006", "Execution & Delivery", "Relentlessly driving high-quality outcomes on schedule with operational excellence.", 5),
    ("COMP-007", "Customer Focus", "Anticipating client needs and aligning organizational priorities around user impact.", 5),
    ("COMP-008", "Problem Solving", "Deconstructing complex, ambiguous problems into structured, data-driven solutions.", 5),
    ("COMP-009", "Adaptability", "Thriving through organizational ambiguity, strategic pivots, and rapid technological change.", 5),
    ("COMP-010", "Integrity & Ethics", "Upholding uncompromised ethical standards, compliance, and transparent decision-making.", 5),
]

DEFAULT_CYCLES = [
    ("CYCLE-2025-H1", "2025 First Half Performance Review", date(2025, 1, 1), date(2025, 6, 30), "closed"),
    ("CYCLE-2025-H2", "2025 Second Half Performance Review", date(2025, 7, 1), date(2025, 12, 31), "closed"),
    ("CYCLE-2026-H1", "2026 First Half Performance Review", date(2026, 1, 1), date(2026, 6, 30), "active"),
    ("CYCLE-2026-H2", "2026 Second Half Performance Review", date(2026, 7, 1), date(2026, 12, 31), "draft"),
]

def seed(db_url: str):
    print(f"[Seeder] Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Seed Competencies
        print("  [1/2] Seeding competencies...")
        for comp_id, name, desc, scale in DEFAULT_COMPETENCIES:
            existing = session.scalar(select(Competency).where(Competency.competency_id == comp_id))
            if not existing:
                comp = Competency(
                    competency_id=comp_id,
                    name=name,
                    description=desc,
                    rating_scale=scale,
                    is_active=True,
                )
                session.add(comp)
            else:
                existing.name = name
                existing.description = desc

        # 2. Seed Review Cycles
        print("  [2/2] Seeding review cycles...")
        for cycle_id, name, start, end, status in DEFAULT_CYCLES:
            existing = session.scalar(select(ReviewCycle).where(ReviewCycle.cycle_id == cycle_id))
            if not existing:
                rc = ReviewCycle(
                    cycle_id=cycle_id,
                    name=name,
                    start_date=start,
                    end_date=end,
                    status=status,
                    version=1,
                )
                session.add(rc)
            else:
                existing.status = status
                existing.name = name

        session.commit()
        print("[Seeder] Reference data successfully seeded!")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PeoplePulse reference data")
    parser.add_argument("--connection-string", default=os.getenv("DATABASE_URL", "sqlite:///./peoplepulse.db"))
    args = parser.parse_args()
    seed(args.connection_string)
