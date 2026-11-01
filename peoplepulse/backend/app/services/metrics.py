"""
PeoplePulse Dashboard Metrics Service
=====================================
Calculates real database-derived KPIs and breakdown statistics.
No numbers are hardcoded.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.models.employee import Employee
from app.models.goal import Goal
from app.models.key_result import KeyResult
from app.models.check_in import CheckIn
from app.models.review import Review
from app.models.review_cycle import ReviewCycle
from app.models.feedback import Feedback
from app.models.issue import Issue
from app.models.audit import AuditEvent
from app.services.progress import calculate_goal_progress


def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Computes real production analytics from the database.
    """
    # 1. Total active employees
    total_employees = db.scalar(
        select(func.count(Employee.id)).where(Employee.employment_status == "active")
    ) or 0

    # 2. Active goals
    active_goals_count = db.scalar(
        select(func.count(Goal.id)).where(Goal.status == "active")
    ) or 0

    # 3. Average goal progress across active goals with KRs
    active_goals = db.scalars(select(Goal).where(Goal.status == "active")).all()
    goal_progress_list = []
    
    for g in active_goals:
        # Load key results
        krs = db.scalars(select(KeyResult).where(KeyResult.goal_id == g.id)).all()
        if krs:
            kr_dicts = [
                {
                    "baseline": float(kr.baseline or 0.0),
                    "actual": float(kr.actual) if kr.actual is not None else None,
                    "target": float(kr.target),
                    "weight": float(kr.weight or 1.0),
                    "metric_type": kr.metric_type,
                    "allowed_scale": float(kr.allowed_progress_scale or 1.0),
                }
                for kr in krs
            ]
            prog_res = calculate_goal_progress(kr_dicts)
            goal_progress_list.append(prog_res["weighted_progress"])

    avg_goal_progress = (
        round(sum(goal_progress_list) / len(goal_progress_list) * 100, 1)
        if goal_progress_list
        else 0.0
    )

    # 4. Check-in count and rate
    total_check_ins = db.scalar(select(func.count(CheckIn.id))) or 0
    # completion rate as check-ins per active employee ratio (capped at 100% or displayed as activity index)
    check_in_rate = (
        round(min((total_check_ins / max(total_employees, 1)) * 100, 100.0), 1)
        if total_employees > 0
        else 0.0
    )

    # 5. Reviews completion rate in active or closed cycles
    total_reviews = db.scalar(select(func.count(Review.id))) or 0
    completed_reviews = db.scalar(
        select(func.count(Review.id)).where(Review.status.in_(["submitted", "approved", "completed", "calibrated"]))
    ) or 0
    review_completion_rate = (
        round((completed_reviews / total_reviews) * 100, 1)
        if total_reviews > 0
        else 0.0
    )

    # 6. Outstanding unacknowledged feedback
    outstanding_feedback = db.scalar(
        select(func.count(Feedback.id)).where(Feedback.status == "submitted")
    ) or 0

    # 7. Unresolved issues / exceptions
    unresolved_issues = db.scalar(
        select(func.count(Issue.id)).where(Issue.resolution_status.in_(["open", "investigating"]))
    ) or 0

    # 8. Department breakdown
    dept_stmt = (
        select(Employee.department, func.count(Employee.id))
        .where(Employee.employment_status == "active")
        .group_by(Employee.department)
        .order_by(func.count(Employee.id).desc())
    )
    dept_rows = db.execute(dept_stmt).all()
    department_breakdown = [
        {"department": dept or "Unassigned", "count": count}
        for dept, count in dept_rows
    ]

    # 9. Recent audit events (last 10)
    recent_audits_stmt = (
        select(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
    )
    recent_audits = [
        {
            "event_id": a.event_id,
            "action": a.action,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "actor_role": a.actor_role,
            "reason": a.reason,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in db.scalars(recent_audits_stmt)
    ]

    # 10. Issue severity breakdown
    issue_sev_stmt = (
        select(Issue.severity, func.count(Issue.id))
        .where(Issue.resolution_status.in_(["open", "investigating"]))
        .group_by(Issue.severity)
    )
    issue_severities = {sev: count for sev, count in db.execute(issue_sev_stmt).all()}

    return {
        "total_employees": total_employees,
        "active_goals": active_goals_count,
        "avg_goal_progress": avg_goal_progress,
        "check_in_completion_rate": check_in_rate,
        "total_check_ins": total_check_ins,
        "total_reviews": total_reviews,
        "completed_reviews": completed_reviews,
        "review_completion_rate": review_completion_rate,
        "outstanding_feedback": outstanding_feedback,
        "unresolved_issues": unresolved_issues,
        "issue_severities": issue_severities,
        "department_breakdown": department_breakdown,
        "recent_audit_events": recent_audits,
    }

