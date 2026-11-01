"""
Loads generated CSV datasets into SQLite or PostgreSQL database for local development.
"""

import csv
import os
import sys
from datetime import datetime, date
from pathlib import Path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.base import Base
from app.models.employee import Employee
from app.models.review_cycle import ReviewCycle
from app.models.competency import Competency
from app.models.goal import Goal
from app.models.key_result import KeyResult
from app.models.check_in import CheckIn, Evidence
from app.models.review import Review
from app.models.feedback import Feedback
from app.models.development_plan import DevelopmentPlan
from app.models.audit import AuditEvent

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "generated"

def parse_date(d_str):
    if not d_str:
        return None
    try:
        return date.fromisoformat(d_str[:10])
    except Exception:
        return None

def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def load_data(db_url: str):
    print(f"[Loader] Connecting to {db_url}...")
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Competencies
        comp_file = DATA_DIR / "competencies.csv"
        if comp_file.exists():
            print("  Loading competencies...")
            with open(comp_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if not session.scalar(select(Competency).where(Competency.competency_id == r["competency_id"])):
                        session.add(Competency(
                            competency_id=r["competency_id"],
                            name=r["name"],
                            description=r.get("description", ""),
                            rating_scale=int(r.get("rating_scale", 5)),
                            is_active=True,
                        ))
            session.commit()

        # 2. Employees
        emp_file = DATA_DIR / "employees.csv"
        if emp_file.exists():
            print("  Loading employees...")
            # First pass: without manager_id
            emp_records = []
            with open(emp_file, "r", encoding="utf-8") as f:
                emp_records = list(csv.DictReader(f))

            for r in emp_records:
                if not session.scalar(select(Employee).where(Employee.employee_id == r["employee_id"])):
                    first = r.get("first_name", "")
                    last = r.get("last_name", "")
                    name = f"{first} {last}".strip() if first or last else r.get("name", "Unknown")
                    session.add(Employee(
                        employee_id=r["employee_id"],
                        name=name,
                        email=r["email"],
                        department=r["department"],
                        job_title=r["job_title"],
                        employment_status=r.get("status", r.get("employment_status", "active")),
                        hire_date=parse_date(r["hire_date"]) or date(2025, 1, 1),
                        termination_date=parse_date(r.get("termination_date")),
                    ))
            session.commit()

            # Second pass: link manager_id
            emp_map = {e.employee_id: e.id for e in session.scalars(select(Employee)).all()}
            for r in emp_records:
                mgr_code = r.get("manager_id")
                if mgr_code and mgr_code in emp_map:
                    emp = session.scalar(select(Employee).where(Employee.employee_id == r["employee_id"]))
                    if emp:
                        emp.manager_id = emp_map[mgr_code]
            session.commit()

        # 3. Review Cycles
        cycle_file = DATA_DIR / "review_cycles.csv"
        if cycle_file.exists():
            print("  Loading review cycles...")
            with open(cycle_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if not session.scalar(select(ReviewCycle).where(ReviewCycle.cycle_id == r["cycle_id"])):
                        session.add(ReviewCycle(
                            cycle_id=r["cycle_id"],
                            name=r["name"],
                            start_date=parse_date(r["start_date"]) or date(2026, 1, 1),
                            end_date=parse_date(r["end_date"]) or date(2026, 6, 30),
                            status=r["status"],
                            version=int(r.get("version", 1)),
                        ))
            session.commit()

        emp_map = {e.employee_id: e.id for e in session.scalars(select(Employee)).all()}
        cycle_map = {c.cycle_id: c.id for c in session.scalars(select(ReviewCycle)).all()}

        # 4. Goals
        goal_file = DATA_DIR / "goals.csv"
        if goal_file.exists():
            print("  Loading goals...")
            with open(goal_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    eid = emp_map.get(r["employee_id"])
                    cid = cycle_map.get(r["cycle_id"])
                    if eid and cid and not session.scalar(select(Goal).where(Goal.goal_id == r["goal_id"])):
                        session.add(Goal(
                            goal_id=r["goal_id"],
                            employee_id=eid,
                            cycle_id=cid,
                            title=r["title"],
                            description=r.get("description"),
                            status=r.get("status", "active"),
                            weight=float(r.get("weight", 1.0)),
                            start_date=parse_date(r.get("start_date")),
                            due_date=parse_date(r.get("due_date")),
                        ))
            session.commit()

        goal_map = {g.goal_id: g.id for g in session.scalars(select(Goal)).all()}

        # 5. Key Results
        kr_file = DATA_DIR / "key_results.csv"
        if kr_file.exists():
            print("  Loading key results...")
            with open(kr_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    gid = goal_map.get(r["goal_id"])
                    kr_id = r.get("kr_id", r.get("key_result_id", ""))
                    if gid and kr_id and not session.scalar(select(KeyResult).where(KeyResult.key_result_id == kr_id)):
                        session.add(KeyResult(
                            key_result_id=kr_id,
                            goal_id=gid,
                            title=r["title"],
                            metric_type="count",
                            unit=r.get("unit", "units"),
                            baseline=0.0,
                            target=float(r.get("target", 100)),
                            actual=float(r["actual"]) if r.get("actual") else None,
                            allowed_progress_scale=float(r.get("allowed_progress_scale", 1.0)),
                        ))
            session.commit()

        # 6. Check-ins
        ci_file = DATA_DIR / "check_ins.csv"
        if ci_file.exists():
            print("  Loading check-ins...")
            with open(ci_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    gid = goal_map.get(r["goal_id"])
                    eid = emp_map.get(r["employee_id"])
                    if gid and eid and not session.scalar(select(CheckIn).where(CheckIn.check_in_id == r["check_in_id"])):
                        goal = session.scalar(select(Goal).where(Goal.id == gid))
                        session.add(CheckIn(
                            check_in_id=r["check_in_id"],
                            employee_id=eid,
                            goal_id=gid,
                            cycle_id=goal.cycle_id if goal else list(cycle_map.values())[0],
                            check_in_date=parse_date(r["check_in_date"]) or date(2026, 1, 1),
                            notes=r.get("notes"),
                            status="submitted",
                        ))
            session.commit()

        # 7. Reviews
        rev_file = DATA_DIR / "reviews.csv"
        if rev_file.exists():
            print("  Loading reviews...")
            with open(rev_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    eid = emp_map.get(r["employee_id"])
                    rid = emp_map.get(r["reviewer_id"])
                    cid = cycle_map.get(r["cycle_id"])
                    rev_id = r.get("review_id", "")
                    if eid and rid and cid and rev_id and not session.scalar(select(Review).where(Review.review_id == rev_id)):
                        session.add(Review(
                            review_id=rev_id,
                            employee_id=eid,
                            cycle_id=cid,
                            reviewer_id=rid,
                            status=r.get("status", "in_progress"),
                            goal_score=float(r.get("self_rating", 3.0)),
                            feedback_score=float(r.get("manager_rating", 3.0)),
                            overall_score=float(r.get("overall_rating", 3.0)),
                            summary=r.get("strengths", r.get("summary", "")),
                            submitted_at=parse_dt(r.get("submitted_at")),
                        ))
            session.commit()

        # 8. Feedback
        fb_file = DATA_DIR / "feedback.csv"
        if fb_file.exists():
            print("  Loading feedback...")
            with open(fb_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    sub_id = emp_map.get(r["subject_employee_id"])
                    auth_id = emp_map.get(r["author_employee_id"])
                    ftype = r.get("feedback_type", "peer")
                    if ftype not in ("self", "manager", "peer"):
                        ftype = "peer"
                    fb_id = r.get("feedback_id", "")
                    if sub_id and fb_id and not session.scalar(select(Feedback).where(Feedback.feedback_id == fb_id)):
                        session.add(Feedback(
                            feedback_id=fb_id,
                            subject_employee_id=sub_id,
                            author_employee_id=auth_id,
                            feedback_type=ftype,
                            comments=r.get("content", r.get("comments", "Good work")),
                            rating=int(float(r.get("rating", 3.0))),
                            submitted_at=parse_dt(r.get("submitted_at")) or datetime(2026, 1, 1),
                            status=r.get("status", "submitted"),
                        ))
            session.commit()

        # 9. Audit Events
        audit_file = DATA_DIR / "audit_events.csv"
        if audit_file.exists():
            print("  Loading audit events...")
            with open(audit_file, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    event_id = r.get("audit_event_id", r.get("event_id", ""))
                    if event_id and not session.scalar(select(AuditEvent).where(AuditEvent.event_id == event_id)):
                        session.add(AuditEvent(
                            event_id=event_id,
                            action=r.get("action", "action"),
                            entity_type=r.get("entity_type", "record"),
                            entity_id=r.get("entity_id", "ID"),
                            reason=r.get("details", r.get("notes")),
                        ))
            session.commit()

        print("[Loader] Data loaded into database successfully!")
    finally:
        session.close()

if __name__ == "__main__":
    db_target = os.getenv("DATABASE_URL", "sqlite:///./peoplepulse.db")
    load_data(db_target)

