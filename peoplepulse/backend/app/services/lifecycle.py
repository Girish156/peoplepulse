"""
Review cycle lifecycle state machine.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.errors import BusinessRuleError, ClosedCycleError

VALID_TRANSITIONS: Dict[str, list[str]] = {
    "draft": ["active"],
    "active": ["closed"],
    "closed": ["archived"],
    "archived": [],
}

MUTABLE_STATUSES = {"draft", "active"}


def can_transition(from_status: str, to_status: str) -> bool:
    """Return True if transition from from_status to to_status is allowed."""
    return to_status in VALID_TRANSITIONS.get(from_status, [])


def can_mutate_cycle(cycle) -> bool:
    """
    Return True if the cycle allows modifications to its child records.

    Closed and archived cycles are immutable without an admin correction.
    """
    return cycle.status in MUTABLE_STATUSES


def transition_cycle(
    cycle,
    new_status: str,
    actor_employee_id: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate and apply a lifecycle transition on *cycle*.

    Parameters
    ----------
    cycle:
        A ``ReviewCycle`` ORM instance.
    new_status:
        Target status string.
    actor_employee_id:
        The employee initiating the transition (may be None for system actions).
    reason:
        Optional human-readable reason for the transition.

    Returns
    -------
    dict
        Audit event data that should be persisted by the caller.

    Raises
    ------
    BusinessRuleError
        If the transition is not allowed from the current status.
    """
    current_status = cycle.status
    allowed = VALID_TRANSITIONS.get(current_status, [])

    if new_status not in allowed:
        raise BusinessRuleError(
            f"Cannot transition review cycle '{cycle.cycle_id}' from "
            f"'{current_status}' to '{new_status}'. "
            f"Allowed transitions: {allowed or 'none (terminal state)'}."
        )

    before_state = {
        "cycle_id": cycle.cycle_id,
        "status": current_status,
        "version": cycle.version,
    }

    cycle.status = new_status
    cycle.version = (cycle.version or 1) + 1

    if new_status == "closed":
        cycle.closed_at = datetime.now(tz=timezone.utc)

    after_state = {
        "cycle_id": cycle.cycle_id,
        "status": new_status,
        "version": cycle.version,
    }

    return {
        "actor_employee_id": actor_employee_id,
        "action": f"cycle.{new_status}",
        "entity_type": "review_cycle",
        "entity_id": cycle.cycle_id,
        "before_state": before_state,
        "after_state": after_state,
        "reason": reason,
    }
