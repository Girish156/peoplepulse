"""
Unit tests for the 5 anomaly categories, ground-truth isolation, and deterministic reproducibility.
"""

from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models
from app.models.employee import Employee
from app.models.review_cycle import ReviewCycle
from app.models.goal import Goal
from app.models.key_result import KeyResult
from app.models.check_in import CheckIn
from app.models.feedback import Feedback
from app.models.audit import AuditEvent
from app.services.anomaly_detection import (
    run_rule_001_goal_owner_mismatch,
    run_rule_002_progress_exceeds_scale,
    run_rule_003_reviewer_no_relationship,
    run_rule_004_closed_cycle_edit,
    run_rule_005_untraceable_feedback,
    run_all_detectors,
)

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_anomaly_rule_001_goal_owner_mismatch(db):
    emp1 = Employee(employee_id="EMP-100001", name="Owner", email="owner@example.com", department="Eng", job_title="Dev", hire_date=date(2026, 1, 1))
    emp2 = Employee(employee_id="EMP-100002", name="Imposter", email="imposter@example.com", department="Eng", job_title="Dev", hire_date=date(2026, 1, 1))
    cycle = ReviewCycle(cycle_id="CYCLE-2026-H1", name="H1", start_date=date(2026, 1, 1), end_date=date(2026, 6, 30))
    db.add_all([emp1, emp2, cycle])
    db.flush()

    goal = Goal(goal_id="GOAL-EMP-100001-001", employee_id=emp1.id, cycle_id=cycle.id, title="Goal 1")
    db.add(goal)
    db.flush()

    # Mismatch: check-in submitted with emp2 for emp1's goal
    ci = CheckIn(check_in_id="CHK-EMP-100002-20260201-001", employee_id=emp2.id, goal_id=goal.id, cycle_id=cycle.id, check_in_date=date(2026, 2, 1))
    db.add(ci)
    db.commit()

    issues = run_rule_001_goal_owner_mismatch(db)
    assert len(issues) == 1
    assert issues[0]["rule_id"] == "RULE-001"
    assert issues[0]["entity_id"] == "CHK-EMP-100002-20260201-001"

def test_anomaly_rule_002_progress_exceeds_scale(db):
    emp = Employee(employee_id="EMP-100003", name="Staff", email="staff@example.com", department="Eng", job_title="Dev", hire_date=date(2026, 1, 1))
    cycle = ReviewCycle(cycle_id="CYCLE-2026-H1", name="H1", start_date=date(2026, 1, 1), end_date=date(2026, 6, 30))
    db.add_all([emp, cycle])
    db.flush()

    goal = Goal(goal_id="GOAL-EMP-100003-001", employee_id=emp.id, cycle_id=cycle.id, title="Goal 2")
    db.add(goal)
    db.flush()

    # Anomaly: KR actual is 250 with target 100 and allowed scale 1.0 (250% > 100%)
    kr = KeyResult(
        key_result_id="KR-GOAL-EMP-100003-001-01",
        goal_id=goal.id,
        title="Excessive progress",
        metric_type="count",
        baseline=0,
        target=100,
        actual=250,
        allowed_progress_scale=1.0,
    )
    db.add(kr)
    db.commit()

    issues = run_rule_002_progress_exceeds_scale(db)
    assert len(issues) == 1
    assert issues[0]["rule_id"] == "RULE-002"
    assert issues[0]["entity_id"] == "KR-GOAL-EMP-100003-001-01"

def test_anomaly_rule_003_reviewer_no_relationship(db):
    mgr = Employee(employee_id="EMP-100004", name="Real Manager", email="mgr@example.com", department="Eng", job_title="Manager", hire_date=date(2026, 1, 1))
    db.add(mgr)
    db.flush()

    emp = Employee(employee_id="EMP-100005", name="Subordinate", email="sub@example.com", department="Eng", job_title="Dev", manager_id=mgr.id, hire_date=date(2026, 1, 1))
    outsider = Employee(employee_id="EMP-100006", name="Outsider", email="out@example.com", department="Sales", job_title="Sales", hire_date=date(2026, 1, 1))
    db.add_all([emp, outsider])
    db.flush()

    # Anomaly: outsider submits manager/downward feedback on emp
    fb = Feedback(
        feedback_id="FBK-100001",
        subject_employee_id=emp.id,
        author_employee_id=outsider.id,
        feedback_type="manager",
        comments="Invalid manager review",
    )
    db.add(fb)
    db.commit()

    issues = run_rule_003_reviewer_no_relationship(db)
    assert len(issues) == 1
    assert issues[0]["rule_id"] == "RULE-003"
    assert issues[0]["entity_id"] == "FBK-100001"

def test_anomaly_rule_004_closed_cycle_edit(db):
    cycle = ReviewCycle(cycle_id="CYCLE-2024-H2", name="Old Cycle", start_date=date(2024, 7, 1), end_date=date(2024, 12, 31), status="closed")
    db.add(cycle)
    db.flush()

    # Anomaly: modification event on closed cycle without authorized correction flag
    audit = AuditEvent(
        event_id="AUD-100000001",
        action="goal.modified",
        entity_type="goal",
        entity_id="GOAL-CYCLE-2024-H2-001",
        before_state={"cycle_id": "CYCLE-2024-H2"},
        after_state={"cycle_id": "CYCLE-2024-H2"},
        reason="Silent unapproved change",
    )
    db.add(audit)
    db.commit()

    issues = run_rule_004_closed_cycle_edit(db)
    assert len(issues) == 1
    assert issues[0]["rule_id"] == "RULE-004"
    assert issues[0]["entity_id"] == "AUD-100000001"

def test_anomaly_rule_005_untraceable_feedback(db):
    emp = Employee(employee_id="EMP-100007", name="Target", email="target@example.com", department="Eng", job_title="Dev", hire_date=date(2026, 1, 1))
    db.add(emp)
    db.flush()

    # Anomaly: feedback with null author
    fb = Feedback(
        feedback_id="FBK-100002",
        subject_employee_id=emp.id,
        author_employee_id=None,
        comments="Ghost feedback",
    )
    db.add(fb)
    db.commit()

    issues = run_rule_005_untraceable_feedback(db)
    assert len(issues) == 1
    assert issues[0]["rule_id"] == "RULE-005"
    assert issues[0]["entity_id"] == "FBK-100002"
