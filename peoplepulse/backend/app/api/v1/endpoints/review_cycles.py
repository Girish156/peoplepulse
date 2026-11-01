from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.db.session import get_db
from app.models.review_cycle import ReviewCycle
from app.schemas.review_cycle import ReviewCycleCreate, ReviewCycleResponse, ReviewCycleTransition
from app.services.lifecycle import transition_cycle
from app.services.audit import create_audit_event

router = APIRouter(prefix="/review-cycles", tags=["Review Cycles"])

@router.get("", response_model=List[ReviewCycleResponse])
def list_review_cycles(db: Session = Depends(get_db)):
    cycles = db.scalars(select(ReviewCycle).order_by(ReviewCycle.start_date.desc())).all()
    return [
        ReviewCycleResponse(
            id=str(c.id),
            cycle_id=c.cycle_id,
            name=c.name,
            start_date=c.start_date,
            end_date=c.end_date,
            status=c.status,
            version=c.version,
            closed_at=c.closed_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cycles
    ]

@router.post("", response_model=ReviewCycleResponse, status_code=status.HTTP_201_CREATED)
def create_review_cycle(payload: ReviewCycleCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(ReviewCycle).where(ReviewCycle.cycle_id == payload.cycle_id))
    if existing:
        raise HTTPException(status_code=409, detail="Review cycle ID already exists")

    c = ReviewCycle(
        cycle_id=payload.cycle_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status or "draft",
        version=1,
    )
    db.add(c)
    db.flush()

    create_audit_event(
        db=db,
        actor_employee_id=None,
        actor_role="admin",
        action="cycle.created",
        entity_type="review_cycle",
        entity_id=c.cycle_id,
        after_state={"cycle_id": c.cycle_id, "status": c.status},
        reason="Cycle created",
    )
    db.commit()
    db.refresh(c)
    return ReviewCycleResponse(
        id=str(c.id),
        cycle_id=c.cycle_id,
        name=c.name,
        start_date=c.start_date,
        end_date=c.end_date,
        status=c.status,
        version=c.version,
        closed_at=c.closed_at,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )

@router.post("/{cycle_id}/transition", response_model=ReviewCycleResponse)
def transition_review_cycle(
    cycle_id: str,
    payload: ReviewCycleTransition,
    db: Session = Depends(get_db),
):
    cycle = db.scalar(
        select(ReviewCycle).where(
            or_(ReviewCycle.id == cycle_id, ReviewCycle.cycle_id == cycle_id)
        )
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Review cycle not found")

    try:
        transition_cycle(cycle, payload.new_status, actor_employee_id=None, reason=payload.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    create_audit_event(
        db=db,
        actor_employee_id=None,
        actor_role="admin",
        action=f"cycle.transitioned_to_{payload.new_status}",
        entity_type="review_cycle",
        entity_id=cycle.cycle_id,
        after_state={"cycle_id": cycle.cycle_id, "status": cycle.status},
        reason=payload.reason or f"Transition to {payload.new_status}",
    )
    db.commit()
    db.refresh(cycle)

    return ReviewCycleResponse(
        id=str(cycle.id),
        cycle_id=cycle.cycle_id,
        name=cycle.name,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
        status=cycle.status,
        version=cycle.version,
        closed_at=cycle.closed_at,
        created_at=cycle.created_at,
        updated_at=cycle.updated_at,
    )

