from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.db.session import get_db
from app.models.issue import Issue
from app.schemas.issue import IssueResponse, IssueResolve
from app.services.anomaly_detection import run_all_detectors, sync_detected_issues_to_db
from app.services.audit import create_audit_event

router = APIRouter(prefix="/issues", tags=["Issues & Exceptions"])

@router.get("", response_model=List[IssueResponse])
def list_issues(
    skip: int = 0,
    limit: int = 50,
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    resolution_status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # First sync detectors so the latest issues from the DB are exposed
    sync_detected_issues_to_db(db)

    stmt = select(Issue)
    if issue_type:
        stmt = stmt.where(Issue.issue_type == issue_type)
    if severity:
        stmt = stmt.where(Issue.severity == severity)
    if resolution_status and isinstance(resolution_status, str):
        stmt = stmt.where(Issue.resolution_status == resolution_status)

    stmt = stmt.order_by(Issue.detected_at.desc()).offset(skip).limit(limit)
    issues = db.scalars(stmt).all()
    return [
        IssueResponse(
            id=str(i.id),
            issue_id=i.issue_id,
            issue_type=i.issue_type,
            entity_type=i.entity_type,
            entity_id=i.entity_id,
            severity=i.severity,
            rule_id=i.rule_id,
            explanation=i.explanation,
            expected_value=i.expected_value,
            actual_value=i.actual_value,
            detected_at=i.detected_at,
            resolution_status=i.resolution_status,
            resolved_at=i.resolved_at,
            resolved_by=str(i.resolved_by) if i.resolved_by else None,
            evidence_refs=i.evidence_refs,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in issues
    ]

@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: str, db: Session = Depends(get_db)):
    i = db.scalar(select(Issue).where(or_(Issue.id == issue_id, Issue.issue_id == issue_id)))
    if not i:
        raise HTTPException(status_code=404, detail="Issue not found")
    return IssueResponse(
        id=str(i.id),
        issue_id=i.issue_id,
        issue_type=i.issue_type,
        entity_type=i.entity_type,
        entity_id=i.entity_id,
        severity=i.severity,
        rule_id=i.rule_id,
        explanation=i.explanation,
        expected_value=i.expected_value,
        actual_value=i.actual_value,
        detected_at=i.detected_at,
        resolution_status=i.resolution_status,
        resolved_at=i.resolved_at,
        resolved_by=str(i.resolved_by) if i.resolved_by else None,
        evidence_refs=i.evidence_refs,
        created_at=i.created_at,
        updated_at=i.updated_at,
    )

@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: str,
    payload: IssueResolve,
    db: Session = Depends(get_db),
):
    i = db.scalar(select(Issue).where(or_(Issue.id == issue_id, Issue.issue_id == issue_id)))
    if not i:
        raise HTTPException(status_code=404, detail="Issue not found")

    i.resolution_status = payload.resolution_status
    i.resolved_at = datetime.now(timezone.utc)

    create_audit_event(
        db=db,
        actor_employee_id=None,
        actor_role="admin",
        action="issue.resolved",
        entity_type="issue",
        entity_id=i.issue_id,
        after_state={"status": i.resolution_status, "notes": payload.notes},
        reason=payload.notes or "Issue resolved by administrator",
    )

    db.commit()
    db.refresh(i)

    return IssueResponse(
        id=str(i.id),
        issue_id=i.issue_id,
        issue_type=i.issue_type,
        entity_type=i.entity_type,
        entity_id=i.entity_id,
        severity=i.severity,
        rule_id=i.rule_id,
        explanation=i.explanation,
        expected_value=i.expected_value,
        actual_value=i.actual_value,
        detected_at=i.detected_at,
        resolution_status=i.resolution_status,
        resolved_at=i.resolved_at,
        resolved_by=str(i.resolved_by) if i.resolved_by else None,
        evidence_refs=i.evidence_refs,
        created_at=i.created_at,
        updated_at=i.updated_at,
    )
