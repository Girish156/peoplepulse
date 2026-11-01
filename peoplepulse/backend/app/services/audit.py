"""
PeoplePulse Audit Service
=========================
Creates and manages immutable audit events for state changes.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

def create_audit_event(
    db: Session,
    actor_employee_id: Optional[str],
    actor_role: Optional[str],
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> AuditEvent:
    """
    Record an immutable audit event for compliance, historical tracing, and anomaly detection.
    """
    # Deterministic or sequence event ID
    # Use random hex or sequence
    seq_hex = uuid.uuid4().hex[:9].upper()
    event_id = f"AUD-{seq_hex}"
    
    event = AuditEvent(
        event_id=event_id,
        actor_employee_id=actor_employee_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_state=before_state,
        after_state=after_state,
        reason=reason,
        correlation_id=correlation_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event

