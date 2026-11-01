"""
Integration tests for FastAPI endpoints and business workflows.
Tests full database interactions, relationships, progress calculations, and audit logging.
"""

from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models
from app.api.v1.endpoints.auth import login, LoginRequest
from app.api.v1.endpoints.employees import create_employee, get_employee, list_employees
from app.api.v1.endpoints.review_cycles import create_review_cycle, list_review_cycles, transition_review_cycle
from app.api.v1.endpoints.goals import create_goal, get_goal, list_goals, update_goal, create_goal_check_in
from app.api.v1.endpoints.check_ins import list_check_ins
from app.api.v1.endpoints.feedback import submit_feedback, list_feedback
from app.api.v1.endpoints.reviews import create_review, submit_review, list_reviews
from app.api.v1.endpoints.development_plans import create_development_plan, approve_development_plan, list_development_plans
from app.api.v1.endpoints.issues import list_issues, resolve_issue
from app.api.v1.endpoints.audit import list_audit_events, get_audit_for_entity
from app.api.v1.endpoints.dashboard import read_dashboard_metrics
from app.api.v1.router import health_check

from app.schemas.employee import EmployeeCreate
from app.schemas.review_cycle import ReviewCycleCreate, ReviewCycleTransition
from app.schemas.goal import GoalCreate, GoalUpdate
from app.schemas.key_result import KeyResultCreate
from app.schemas.check_in import CheckInCreate, EvidenceCreate
from app.schemas.feedback import FeedbackCreate
from app.schemas.review import ReviewCreate, ReviewSubmit
from app.schemas.development_plan import DevelopmentPlanCreate, DevelopmentPlanActionCreate
from app.schemas.issue import IssueResolve

# In-memory SQLite engine for complete test isolation
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

def test_health_endpoint():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["service"] == "peoplepulse-backend"

def test_auth_login():
    res = login(LoginRequest(email="admin@peoplepulse.demo", password="PeoplePulse2026!"))
    assert res.role == "admin"
    assert res.access_token is not None

def test_employee_crud(db):
    emp_in = EmployeeCreate(
        employee_id="EMP-900001",
        name="Alice Engineer",
        email="alice@example.com",
        department="Engineering",
        job_title="Staff Engineer",
        employment_status="active",
        hire_date=date(2026, 1, 1),
    )
    created = create_employee(emp_in, db=db)
    assert created.employee_id == "EMP-900001"
    assert created.name == "Alice Engineer"

    fetched = get_employee("EMP-900001", db=db)
    assert fetched.email == "alice@example.com"

    listed = list_employees(department="Engineering", db=db)
    assert len(listed) == 1
    assert listed[0].employee_id == "EMP-900001"

def test_goal_with_key_results_and_checkin_flow(db):
    # 1. Create employee
    emp = create_employee(
        EmployeeCreate(
            employee_id="EMP-900002",
            name="Charlie Product",
            email="charlie@example.com",
            department="Product",
            job_title="Director of Product",
            hire_date=date(2026, 1, 1),
        ),
        db=db,
    )

    # 2. Create review cycle
    cycle = create_review_cycle(
        ReviewCycleCreate(
            cycle_id="CYCLE-2026-H1",
            name="2026 H1 Review",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            status="active",
        ),
        db=db,
    )

    # 3. Create goal with key results
    # Spec example: KR1: target=10, actual=8, w=0.6; KR2: target=20, actual=15, w=0.4 -> 78%
    goal = create_goal(
        GoalCreate(
            goal_id="GOAL-EMP-900002-001",
            employee_employee_id="EMP-900002",
            cycle_cycle_id="CYCLE-2026-H1",
            title="Q1 Product Launch",
            description="Deliver high value MVP",
            status="active",
            key_results=[
                KeyResultCreate(
                    key_result_id="KR-GOAL-EMP-900002-001-01",
                    title="Deliver 10 features",
                    metric_type="count",
                    baseline=0,
                    target=10,
                    actual=8,
                    weight=0.6,
                ),
                KeyResultCreate(
                    key_result_id="KR-GOAL-EMP-900002-001-02",
                    title="Run 20 tests",
                    metric_type="count",
                    baseline=0,
                    target=20,
                    actual=15,
                    weight=0.4,
                ),
            ],
        ),
        db=db,
    )
    assert goal.progress_percentage == 78.0

    # 4. Submit check-in with evidence
    ci = create_goal_check_in(
        goal_id=goal.id,
        payload=CheckInCreate(
            employee_employee_id="EMP-900002",
            goal_goal_id="GOAL-EMP-900002-001",
            check_in_date=date(2026, 2, 15),
            notes="Completed features on track",
            progress_snapshot={"KR-GOAL-EMP-900002-001-01": 9.0},
            evidence=[
                EvidenceCreate(
                    title="Sprint Review Video",
                    url="https://example.com/video/sprint-1",
                    evidence_type="url",
                )
            ],
        ),
        db=db,
    )
    assert ci.goal_title == "Q1 Product Launch"
    assert len(ci.evidence) == 1

    # 5. Check dashboard metrics derived from database
    metrics = read_dashboard_metrics(db=db)
    assert metrics["total_employees"] == 1
    assert metrics["active_goals"] == 1
    assert metrics["total_check_ins"] == 1
    assert metrics["avg_goal_progress"] > 0

    # 6. Verify audit history was captured
    audits = get_audit_for_entity("goal", "GOAL-EMP-900002-001", db=db)
    assert len(audits) >= 1
    assert audits[0].action == "goal.created"

def test_review_cycle_transitions_and_review_workflow(db):
    # Create employee and manager
    mgr = create_employee(
        EmployeeCreate(
            employee_id="EMP-900010",
            name="Manager Mary",
            email="mary@example.com",
            department="Engineering",
            job_title="Engineering Manager",
            hire_date=date(2025, 1, 1),
        ),
        db=db,
    )
    dev = create_employee(
        EmployeeCreate(
            employee_id="EMP-900011",
            name="Dev Dave",
            email="dave@example.com",
            department="Engineering",
            job_title="Software Engineer",
            manager_employee_id="EMP-900010",
            hire_date=date(2025, 6, 1),
        ),
        db=db,
    )

    cycle = create_review_cycle(
        ReviewCycleCreate(
            cycle_id="CYCLE-2025-Q4",
            name="2025 Q4 Review",
            start_date=date(2025, 10, 1),
            end_date=date(2025, 12, 31),
            status="draft",
        ),
        db=db,
    )

    # Transition draft -> active
    transition_review_cycle(
        cycle.id,
        ReviewCycleTransition(new_status="active", reason="Opening cycle"),
        db=db,
    )

    # Initiate review
    rev = create_review(
        ReviewCreate(
            employee_id="EMP-900011",
            cycle_id="CYCLE-2025-Q4",
            reviewer_id="EMP-900010",
            summary="Annual performance assessment",
        ),
        db=db,
    )
    assert rev.status == "pending"

    # Submit review
    submitted = submit_review(
        rev.id,
        ReviewSubmit(goal_score=4.5, feedback_score=4.0),
        db=db,
    )
    assert submitted.status == "submitted"
    assert submitted.overall_score == 4.25

    # Create development plan
    dev_plan = create_development_plan(
        DevelopmentPlanCreate(
            employee_id="EMP-900011",
            review_id=submitted.id,
            objectives="Level up technical leadership skills",
            actions=[
                DevelopmentPlanActionCreate(
                    title="Lead system design workshop",
                    due_date=date(2026, 4, 1),
                )
            ],
        ),
        db=db,
    )
    assert dev_plan.status == "active"

    # Approve development plan
    approved_plan = approve_development_plan(dev_plan.id, db=db)
    assert approved_plan.status == "completed"


def test_feedback_manager_relationship_enforced(db):
    mgr = create_employee(
        EmployeeCreate(
            employee_id="EMP-900020",
            name="Mgr One",
            email="mgrone@example.com",
            department="Engineering",
            job_title="Manager",
            hire_date=date(2025, 1, 1),
        ),
        db=db,
    )
    outsider = create_employee(
        EmployeeCreate(
            employee_id="EMP-900021",
            name="Outsider",
            email="outsider@example.com",
            department="Sales",
            job_title="AE",
            hire_date=date(2025, 1, 1),
        ),
        db=db,
    )
    report = create_employee(
        EmployeeCreate(
            employee_id="EMP-900022",
            name="Report",
            email="report@example.com",
            department="Engineering",
            job_title="Engineer",
            manager_employee_id="EMP-900020",
            hire_date=date(2025, 6, 1),
        ),
        db=db,
    )
    from fastapi import HTTPException

    try:
        submit_feedback(
            FeedbackCreate(
                subject_employee_id="EMP-900022",
                author_employee_id="EMP-900021",
                feedback_type="manager",
                comments="Unauthorized manager feedback",
                rating=3,
            ),
            db=db,
        )
        assert False, "Expected 403 for unauthorized manager feedback"
    except HTTPException as exc:
        assert exc.status_code == 403


def test_closed_cycle_rejects_goal_create(db):
    create_employee(
        EmployeeCreate(
            employee_id="EMP-900030",
            name="Closed Cycle Emp",
            email="closed@example.com",
            department="Finance",
            job_title="Analyst",
            hire_date=date(2025, 1, 1),
        ),
        db=db,
    )
    create_review_cycle(
        ReviewCycleCreate(
            cycle_id="CYCLE-CLOSED-01",
            name="Closed Cycle",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30),
            status="draft",
        ),
        db=db,
    )
    transition_review_cycle("CYCLE-CLOSED-01", ReviewCycleTransition(new_status="active"), db=db)
    transition_review_cycle("CYCLE-CLOSED-01", ReviewCycleTransition(new_status="closed"), db=db)
    from fastapi import HTTPException

    try:
        create_goal(
            GoalCreate(
                employee_employee_id="EMP-900030",
                cycle_cycle_id="CYCLE-CLOSED-01",
                title="Should fail",
            ),
            db=db,
        )
        assert False, "Expected 409 for closed cycle mutation"
    except HTTPException as exc:
        assert exc.status_code == 409


def test_http_health_not_found_and_admin_auth():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        missing = client.get("/api/v1/employees/EMP-DOES-NOT-EXIST")
        assert missing.status_code == 404
        unauth = client.get("/api/v1/admin/validation-report")
        assert unauth.status_code in (401, 403)
        login_res = client.post(
            "/api/v1/auth/token",
            json={"email": "admin@peoplepulse.demo", "password": "PeoplePulse2026!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        forbidden = client.post(
            "/api/v1/admin/generate-data",
            json={"mode": "small", "seed": 20261022},
            headers={"Authorization": "Bearer not-a-token"},
        )
        assert forbidden.status_code == 401
        # Employee role cannot generate data
        emp_login = client.post(
            "/api/v1/auth/token",
            json={"email": "employee@peoplepulse.demo", "password": "PeoplePulse2026!"},
        )
        emp_token = emp_login.json()["access_token"]
        denied = client.post(
            "/api/v1/admin/generate-data",
            json={"mode": "small", "seed": 20261022},
            headers={"Authorization": f"Bearer {emp_token}"},
        )
        assert denied.status_code == 403
        allowed = client.get(
            "/api/v1/admin/jobs/does-not-exist",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert allowed.status_code == 404
