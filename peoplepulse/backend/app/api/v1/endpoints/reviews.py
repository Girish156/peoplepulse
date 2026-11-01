from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.db.session import get_db
from app.models.review import Review, ReviewParticipant
from app.models.employee import Employee
from app.models.review_cycle import ReviewCycle
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewSubmit, ReviewParticipantResponse
from app.services.audit import create_audit_event
from app.services.lifecycle import can_mutate_cycle

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.get("", response_model=List[ReviewResponse])
def list_reviews(
    skip: int = 0,
    limit: int = 50,
    employee_id: Optional[str] = None,
    cycle_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Review)
    if employee_id:
        emp = db.scalar(select(Employee).where(or_(Employee.id == employee_id, Employee.employee_id == employee_id)))
        if emp:
            stmt = stmt.where(Review.employee_id == emp.id)
    if cycle_id:
        cycle = db.scalar(select(ReviewCycle).where(or_(ReviewCycle.id == cycle_id, ReviewCycle.cycle_id == cycle_id)))
        if cycle:
            stmt = stmt.where(Review.cycle_id == cycle.id)

    stmt = stmt.order_by(Review.created_at.desc()).offset(skip).limit(limit)
    reviews = db.scalars(stmt).all()

    emp_map = {e.id: e for e in db.scalars(select(Employee)).all()}
    cycle_map = {c.id: c for c in db.scalars(select(ReviewCycle)).all()}

    results = []
    for r in reviews:
        emp = emp_map.get(r.employee_id)
        reviewer = emp_map.get(r.reviewer_id)
        cycle = cycle_map.get(r.cycle_id)
        participants = db.scalars(select(ReviewParticipant).where(ReviewParticipant.review_id == r.id)).all()
        part_responses = [
            ReviewParticipantResponse(
                id=str(p.id),
                participant_employee_id=str(p.participant_employee_id),
                participant_name=emp_map.get(p.participant_employee_id).name if emp_map.get(p.participant_employee_id) else None,
                role=p.role,
                is_required=p.is_required,
                completed_at=p.completed_at,
            )
            for p in participants
        ]
        results.append(
            ReviewResponse(
                id=str(r.id),
                review_id=r.review_id,
                employee_id=str(r.employee_id),
                cycle_id=str(r.cycle_id),
                reviewer_id=str(r.reviewer_id),
                employee_name=emp.name if emp else None,
                reviewer_name=reviewer.name if reviewer else None,
                cycle_name=cycle.name if cycle else None,
                status=r.status,
                goal_score=float(r.goal_score) if r.goal_score is not None else None,
                feedback_score=float(r.feedback_score) if r.feedback_score is not None else None,
                overall_score=float(r.overall_score) if r.overall_score is not None else None,
                summary=r.summary,
                submitted_at=r.submitted_at,
                version=r.version,
                participants=part_responses,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return results

@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: str, db: Session = Depends(get_db)):
    r = db.scalar(select(Review).where(or_(Review.id == review_id, Review.review_id == review_id)))
    if not r:
        raise HTTPException(status_code=404, detail="Review not found")
    emp_map = {e.id: e for e in db.scalars(select(Employee)).all()}
    cycle = db.scalar(select(ReviewCycle).where(ReviewCycle.id == r.cycle_id))
    emp = emp_map.get(r.employee_id)
    reviewer = emp_map.get(r.reviewer_id)
    participants = db.scalars(select(ReviewParticipant).where(ReviewParticipant.review_id == r.id)).all()
    return ReviewResponse(
        id=str(r.id),
        review_id=r.review_id,
        employee_id=str(r.employee_id),
        cycle_id=str(r.cycle_id),
        reviewer_id=str(r.reviewer_id),
        employee_name=emp.name if emp else None,
        reviewer_name=reviewer.name if reviewer else None,
        cycle_name=cycle.name if cycle else None,
        status=r.status,
        goal_score=float(r.goal_score) if r.goal_score is not None else None,
        feedback_score=float(r.feedback_score) if r.feedback_score is not None else None,
        overall_score=float(r.overall_score) if r.overall_score is not None else None,
        summary=r.summary,
        submitted_at=r.submitted_at,
        version=r.version,
        participants=[
            ReviewParticipantResponse(
                id=str(p.id),
                participant_employee_id=str(p.participant_employee_id),
                participant_name=emp_map.get(p.participant_employee_id).name if emp_map.get(p.participant_employee_id) else None,
                role=p.role,
                is_required=p.is_required,
                completed_at=p.completed_at,
            )
            for p in participants
        ],
        created_at=r.created_at,
        updated_at=r.updated_at,
    )

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)):
    emp = db.scalar(select(Employee).where(or_(Employee.id == payload.employee_id, Employee.employee_id == payload.employee_id)))
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    reviewer = db.scalar(select(Employee).where(or_(Employee.id == payload.reviewer_id, Employee.employee_id == payload.reviewer_id)))
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer not found")

    cycle = db.scalar(select(ReviewCycle).where(or_(ReviewCycle.id == payload.cycle_id, ReviewCycle.cycle_id == payload.cycle_id)))
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")

    if not can_mutate_cycle(cycle):
        raise HTTPException(status_code=409, detail=f"Cannot initiate reviews in a {cycle.status} cycle")

    r_id = payload.review_id
    if not r_id:
        count = db.scalar(select(func.count(Review.id))) or 0
        r_id = f"REV-2026-{count+1:06d}"

    review = Review(
        review_id=r_id,
        employee_id=emp.id,
        cycle_id=cycle.id,
        reviewer_id=reviewer.id,
        status="pending",
        summary=payload.summary,
        version=1,
    )
    db.add(review)
    db.flush()

    create_audit_event(
        db=db,
        actor_employee_id=str(reviewer.id),
        actor_role="manager",
        action="review.initiated",
        entity_type="review",
        entity_id=review.review_id,
        after_state={"review_id": review.review_id, "employee": emp.employee_id},
        reason="Review initialized",
    )

    db.commit()
    db.refresh(review)
    return ReviewResponse(
        id=str(review.id),
        review_id=review.review_id,
        employee_id=str(review.employee_id),
        cycle_id=str(review.cycle_id),
        reviewer_id=str(review.reviewer_id),
        employee_name=emp.name,
        reviewer_name=reviewer.name,
        cycle_name=cycle.name,
        status=review.status,
        goal_score=None,
        feedback_score=None,
        overall_score=None,
        summary=review.summary,
        submitted_at=None,
        version=review.version,
        participants=[],
        created_at=review.created_at,
        updated_at=review.updated_at,
    )

@router.post("/{review_id}/submit", response_model=ReviewResponse)
def submit_review(
    review_id: str,
    payload: ReviewSubmit,
    db: Session = Depends(get_db),
):
    review = db.scalar(select(Review).where(or_(Review.id == review_id, Review.review_id == review_id)))
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    cycle = db.scalar(select(ReviewCycle).where(ReviewCycle.id == review.cycle_id))
    if cycle and not can_mutate_cycle(cycle):
        raise HTTPException(status_code=409, detail=f"Cannot submit reviews for a {cycle.status} cycle")

    review.status = "submitted"
    review.submitted_at = datetime.now(timezone.utc)
    if payload.summary is not None:
        review.summary = payload.summary
    if payload.goal_score is not None:
        review.goal_score = payload.goal_score
    if payload.feedback_score is not None:
        review.feedback_score = payload.feedback_score
    if payload.overall_score is not None:
        review.overall_score = payload.overall_score
    elif payload.goal_score is not None and payload.feedback_score is not None:
        review.overall_score = round(payload.goal_score * 0.5 + payload.feedback_score * 0.5, 2)

    review.version += 1

    create_audit_event(
        db=db,
        actor_employee_id=str(review.reviewer_id),
        actor_role="manager",
        action="review.submitted",
        entity_type="review",
        entity_id=review.review_id,
        after_state={"review_id": review.review_id, "overall_score": float(review.overall_score or 0)},
        reason="Final review submitted",
    )

    db.commit()
    db.refresh(review)

    emp = db.scalar(select(Employee).where(Employee.id == review.employee_id))
    rev = db.scalar(select(Employee).where(Employee.id == review.reviewer_id))
    return ReviewResponse(
        id=str(review.id),
        review_id=review.review_id,
        employee_id=str(review.employee_id),
        cycle_id=str(review.cycle_id),
        reviewer_id=str(review.reviewer_id),
        employee_name=emp.name if emp else None,
        reviewer_name=rev.name if rev else None,
        cycle_name=cycle.name if cycle else None,
        status=review.status,
        goal_score=float(review.goal_score) if review.goal_score is not None else None,
        feedback_score=float(review.feedback_score) if review.feedback_score is not None else None,
        overall_score=float(review.overall_score) if review.overall_score is not None else None,
        summary=review.summary,
        submitted_at=review.submitted_at,
        version=review.version,
        participants=[],
        created_at=review.created_at,
        updated_at=review.updated_at,
    )

