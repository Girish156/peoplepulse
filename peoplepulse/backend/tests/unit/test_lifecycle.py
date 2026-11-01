"""
Unit tests for review cycle lifecycle states.
Verifies permitted transitions and rejection of invalid/closed transitions.
"""

import pytest
from app.core.errors import BusinessRuleError
from app.models.review_cycle import ReviewCycle
from app.services.lifecycle import transition_cycle, can_mutate_cycle, can_transition

def test_valid_cycle_transitions():
    cycle = ReviewCycle(
        cycle_id="CYCLE-TEST-01",
        name="Test Cycle",
        start_date="2026-01-01",
        end_date="2026-06-30",
        status="draft",
        version=1,
    )
    # draft -> active
    assert can_transition("draft", "active") is True
    transition_cycle(cycle, "active")
    assert cycle.status == "active"
    assert cycle.version == 2
    assert can_mutate_cycle(cycle) is True

    # active -> closed
    assert can_transition("active", "closed") is True
    transition_cycle(cycle, "closed")
    assert cycle.status == "closed"
    assert cycle.closed_at is not None
    assert can_mutate_cycle(cycle) is False

    # closed -> archived
    assert can_transition("closed", "archived") is True
    transition_cycle(cycle, "archived")
    assert cycle.status == "archived"
    assert can_mutate_cycle(cycle) is False

def test_invalid_cycle_transitions():
    cycle = ReviewCycle(
        cycle_id="CYCLE-TEST-02",
        name="Test Cycle",
        start_date="2026-01-01",
        end_date="2026-06-30",
        status="draft",
        version=1,
    )
    # Cannot jump draft -> closed
    assert can_transition("draft", "closed") is False
    with pytest.raises((BusinessRuleError, ValueError)):
        transition_cycle(cycle, "closed")

    # Cannot transition out of archived
    cycle.status = "archived"
    assert can_transition("archived", "active") is False
    with pytest.raises((BusinessRuleError, ValueError)):
        transition_cycle(cycle, "active")
