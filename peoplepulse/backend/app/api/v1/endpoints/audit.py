from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    skip: int = 0,
    limit: int = 50,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(AuditEvent)
    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditEvent.action == action)

    stmt = stmt.order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit)
    events = db.scalars(stmt).all()
    return [
        AuditEventResponse(
            id=str(e.id),
            event_id=e.event_id,
            actor_employee_id=str(e.actor_employee_id) if e.actor_employee_id else None,
            actor_role=e.actor_role,
            action=e.action,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            before_state=e.before_state,
            after_state=e.after_state,
            reason=e.reason,
            correlation_id=e.correlation_id,
            created_at=e.created_at,
        )
        for e in events
    ]

@router.get("/{entity_type}/{entity_id}", response_model=List[AuditEventResponse])
def get_audit_for_entity(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
):
    stmt = (
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == entity_type,
            AuditEvent.entity_id == entity_id,
        )
        .order_by(AuditEvent.created_at.desc())
    )
    events = db.scalars(stmt).all()
    return [
        AuditEventResponse(
            id=str(e.id),
            event_id=e.event_id,
            actor_employee_id=str(e.actor_employee_id) if e.actor_employee_id else None,
            actor_role=e.actor_role,
            action=e.action,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            before_state=e.before_state,
            after_state=e.after_state,
            reason=e.reason,
            correlation_id=e.correlation_id,
            created_at=e.created_at,
        )
        for e in events
    ]

