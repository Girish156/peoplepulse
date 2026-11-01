"""
PeoplePulse Anomaly Detection Service
=====================================
Deterministic, rule-based anomaly detector for data quality and integrity violations.
CRITICAL: Never imports from ground_truth paths. Operates solely on database state.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.goal import Goal
from app.models.key_result import KeyResult
from app.models.check_in import CheckIn
from app.models.feedback import Feedback
from app.models.employee import Employee
from app.models.audit import AuditEvent
from app.models.review_cycle import ReviewCycle
from app.models.issue import Issue


def run_rule_001_goal_owner_mismatch(db: Session) -> List[Dict[str, Any]]:
    """
    RULE-001: goal_owner_mismatch
    Check-in employee_id != Goal employee_id.
    """
    issues = []
    # Query check-ins and join with goal
    stmt = (
        select(CheckIn, Goal)
        .join(Goal, CheckIn.goal_id == Goal.id)
    )
    for ci, goal in db.execute(stmt):
        if ci.employee_id != goal.employee_id:
            issues.append({
                "rule_id": "RULE-001",
                "issue_type": "goal_owner_mismatch",
                "entity_type": "check_in",
                "entity_id": ci.check_in_id,
                "severity": "high",
                "explanation": f"Check-in {ci.check_in_id} was submitted for goal {goal.goal_id} by an employee other than the goal owner.",
                "expected_value": str(goal.employee_id),
                "actual_value": str(ci.employee_id),
                "evidence_refs": [ci.check_in_id, goal.goal_id],
            })
    return issues


def run_rule_002_progress_exceeds_scale(db: Session) -> List[Dict[str, Any]]:
    """
    RULE-002: progress_exceeds_scale
    Key result actual value exceeds allowed_progress_scale without rationale.
    """
    issues = []
    stmt = select(KeyResult)
    for kr in db.scalars(stmt):
        if kr.target and kr.actual is not None:
            baseline = float(kr.baseline or 0.0)
            target = float(kr.target)
            actual = float(kr.actual)
            scale = float(kr.allowed_progress_scale or 1.0)
            span = target - baseline
            if span > 0:
                progress = (actual - baseline) / span
                if progress > scale:
                    issues.append({
                        "rule_id": "RULE-002",
                        "issue_type": "progress_exceeds_scale",
                        "entity_type": "key_result",
                        "entity_id": kr.key_result_id,
                        "severity": "medium",
                        "explanation": f"Key result {kr.key_result_id} progress ({progress:.1%}) exceeds maximum allowed scale ({scale:.1%}) without approved variance rationale.",
                        "expected_value": f"<= {scale:.2f}",
                        "actual_value": f"{progress:.2f}",
                        "evidence_refs": [kr.key_result_id],
                    })
    return issues


def run_rule_003_reviewer_no_relationship(db: Session) -> List[Dict[str, Any]]:
    """
    RULE-003: reviewer_no_relationship
    Feedback author has no legitimate supervisory or peer relationship to subject.
    """
    issues = []
    # Map employees to their manager_id
    emp_map = {e.id: e for e in db.scalars(select(Employee))}
    
    stmt = select(Feedback)
    for fb in db.scalars(stmt):
        subject = emp_map.get(fb.subject_employee_id)
        author = emp_map.get(fb.author_employee_id)
        
        if not subject or not author:
            continue
            
        fb_type = fb.feedback_type or "peer"
        is_invalid = False
        reason = ""
        
        if fb_type == "manager" or fb_type == "downward":
            if subject.manager_id != author.id:
                is_invalid = True
                reason = f"Manager feedback author {author.employee_id} is not the designated manager of {subject.employee_id}"
        elif fb_type == "upward":
            if author.manager_id != subject.id:
                is_invalid = True
                reason = f"Upward feedback subject {subject.employee_id} is not the manager of {author.employee_id}"
        elif fb_type == "self":
            if author.id != subject.id:
                is_invalid = True
                reason = f"Self feedback author {author.employee_id} does not match subject {subject.employee_id}"
                
        if is_invalid:
            issues.append({
                "rule_id": "RULE-003",
                "issue_type": "reviewer_no_relationship",
                "entity_type": "feedback",
                "entity_id": fb.feedback_id,
                "severity": "high",
                "explanation": reason,
                "expected_value": "Valid reporting line or authorized participation",
                "actual_value": f"Author: {author.employee_id}, Subject: {subject.employee_id}",
                "evidence_refs": [fb.feedback_id],
            })
    return issues


def run_rule_004_closed_cycle_edit(db: Session) -> List[Dict[str, Any]]:
    """
    RULE-004: closed_cycle_edit
    Modification applied to entities belonging to a closed or archived cycle without authorized correction flag.
    """
    issues = []
    # Identify closed cycles
    closed_cycles = {c.cycle_id for c in db.scalars(select(ReviewCycle).where(ReviewCycle.status.in_(["closed", "archived"])))}
    
    stmt = select(AuditEvent).where(AuditEvent.action.ilike("%modified%"))
    for event in db.scalars(stmt):
        # Check if event affects a closed cycle entity
        entity_id = event.entity_id or ""
        reason = event.reason or ""
        is_authorized = "authorized" in reason.lower()
        
        # Check before/after state for cycle references
        cycle_ref = None
        if event.before_state and isinstance(event.before_state, dict):
            cycle_ref = event.before_state.get("cycle_id")
        if not cycle_ref and event.after_state and isinstance(event.after_state, dict):
            cycle_ref = event.after_state.get("cycle_id")
            
        if (cycle_ref in closed_cycles or any(c in entity_id for c in closed_cycles)) and not is_authorized:
            issues.append({
                "rule_id": "RULE-004",
                "issue_type": "closed_cycle_edit",
                "entity_type": "audit_event",
                "entity_id": event.event_id,
                "severity": "critical",
                "explanation": f"Unsanctioned edit detected on closed/archived cycle entity {event.entity_id} without authorized versioning override.",
                "expected_value": "Closed cycle immutable without authorized correction flag",
                "actual_value": f"Action: {event.action}",
                "evidence_refs": [event.event_id],
            })
    return issues


def run_rule_005_untraceable_feedback(db: Session) -> List[Dict[str, Any]]:
    """
    RULE-005: untraceable_feedback
    Feedback record submitted with null, missing, or nonexistent author employee ID.
    """
    issues = []
    valid_emp_ids = set(db.scalars(select(Employee.id)).all())
    stmt = select(Feedback)
    for fb in db.scalars(stmt):
        if fb.author_employee_id is None or fb.author_employee_id not in valid_emp_ids:
            issues.append({
                "rule_id": "RULE-005",
                "issue_type": "untraceable_feedback",
                "entity_type": "feedback",
                "entity_id": fb.feedback_id,
                "severity": "critical",
                "explanation": f"Feedback record {fb.feedback_id} has missing or unresolvable author attribution.",
                "expected_value": "Valid existing employee ID reference",
                "actual_value": str(fb.author_employee_id),
                "evidence_refs": [fb.feedback_id],
            })
    return issues


def run_all_detectors(db: Session) -> List[Dict[str, Any]]:
    """
    Executes all anomaly detection rules against the database and returns structured issue descriptors.
    """
    issues = []
    issues.extend(run_rule_001_goal_owner_mismatch(db))
    issues.extend(run_rule_002_progress_exceeds_scale(db))
    issues.extend(run_rule_003_reviewer_no_relationship(db))
    issues.extend(run_rule_004_closed_cycle_edit(db))
    issues.extend(run_rule_005_untraceable_feedback(db))
    return issues


def sync_detected_issues_to_db(db: Session) -> int:
    """
    Detects anomalies and persists/updates them in the `issues` table.
    """
    detected_issues = run_all_detectors(db)
    synced = 0
    now = datetime.now(timezone.utc)
    
    for item in detected_issues:
        existing = db.scalar(
            select(Issue).where(
                Issue.rule_id == item["rule_id"],
                Issue.entity_id == item["entity_id"]
            )
        )
        if not existing:
            issue_id = f"ISS-{uuid.uuid4().hex[:9].upper()}"
            issue = Issue(
                issue_id=issue_id,
                issue_type=item["issue_type"],
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                severity=item["severity"],
                rule_id=item["rule_id"],
                explanation=item["explanation"],
                expected_value=item.get("expected_value"),
                actual_value=item.get("actual_value"),
                detected_at=now,
                resolution_status="open",
                evidence_refs=item.get("evidence_refs"),
            )
            db.add(issue)
            synced += 1
            
    db.commit()
    return synced
