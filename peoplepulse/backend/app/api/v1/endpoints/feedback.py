from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.db.session import get_db
from app.models.feedback import Feedback
from app.models.employee import Employee
from app.models.competency import Competency
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.audit import create_audit_event

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.get("", response_model=List[FeedbackResponse])
def list_feedback(
    skip: int = 0,
    limit: int = 50,
    subject_id: Optional[str] = None,
    author_id: Optional[str] = None,
    feedback_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Feedback)
    if subject_id:
        sub = db.scalar(select(Employee).where(or_(Employee.id == subject_id, Employee.employee_id == subject_id)))
        if sub:
            stmt = stmt.where(Feedback.subject_employee_id == sub.id)
    if author_id:
        auth = db.scalar(select(Employee).where(or_(Employee.id == author_id, Employee.employee_id == author_id)))
        if auth:
            stmt = stmt.where(Feedback.author_employee_id == auth.id)
    if feedback_type:
        stmt = stmt.where(Feedback.feedback_type == feedback_type)

    stmt = stmt.order_by(Feedback.submitted_at.desc()).offset(skip).limit(limit)
    feedbacks = db.scalars(stmt).all()

    emp_map = {e.id: e for e in db.scalars(select(Employee)).all()}
    comp_map = {c.id: c for c in db.scalars(select(Competency)).all()}

    results = []
    for fb in feedbacks:
        sub = emp_map.get(fb.subject_employee_id)
        auth = emp_map.get(fb.author_employee_id)
        comp = comp_map.get(fb.competency_id) if fb.competency_id else None
        results.append(
            FeedbackResponse(
                id=str(fb.id),
                feedback_id=fb.feedback_id,
                subject_employee_id=str(fb.subject_employee_id),
                author_employee_id=str(fb.author_employee_id),
                subject_name=sub.name if sub else None,
                author_name=auth.name if auth else None,
                feedback_type=fb.feedback_type,
                competency_name=comp.name if comp else None,
                rating=fb.rating,
                comments=fb.comments,
                status=fb.status,
                submitted_at=fb.submitted_at,
                created_at=fb.created_at,
                updated_at=fb.updated_at,
            )
        )
    return results

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    sub = db.scalar(
        select(Employee).where(
            or_(Employee.id == payload.subject_employee_id, Employee.employee_id == payload.subject_employee_id)
        )
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subject employee not found")

    auth = db.scalar(
        select(Employee).where(
            or_(Employee.id == payload.author_employee_id, Employee.employee_id == payload.author_employee_id)
        )
    )
    if not auth:
        raise HTTPException(status_code=404, detail="Author employee not found")

    # Validate relationship rules
    if payload.feedback_type == "self" and sub.id != auth.id:
        raise HTTPException(status_code=400, detail="Self feedback author must match subject")
    if payload.feedback_type == "manager" and sub.manager_id != auth.id:
        raise HTTPException(status_code=403, detail="Manager feedback must be submitted by the employee's direct manager")

    comp_id = None
    if payload.competency_id:
        comp = db.scalar(
            select(Competency).where(
                or_(Competency.id == payload.competency_id, Competency.competency_id == payload.competency_id)
            )
        )
        if comp:
            comp_id = comp.id

    fb_id = payload.feedback_id
    if not fb_id:
        count = db.scalar(select(func.count(Feedback.id))) or 0
        fb_id = f"FBK-{count + 1:06d}"

    fb = Feedback(
        feedback_id=fb_id,
        subject_employee_id=sub.id,
        author_employee_id=auth.id,
        review_id=payload.review_id,
        feedback_type=payload.feedback_type,
        competency_id=comp_id,
        rating=payload.rating,
        comments=payload.comments,
        status="submitted",
    )
    db.add(fb)
    db.flush()

    create_audit_event(
        db=db,
        actor_employee_id=str(auth.id),
        actor_role="employee",
        action="feedback.submitted",
        entity_type="feedback",
        entity_id=fb.feedback_id,
        after_state={"feedback_id": fb.feedback_id, "subject": sub.employee_id, "type": fb.feedback_type},
        reason="Feedback submitted",
    )

    db.commit()
    db.refresh(fb)

    comp = db.scalar(select(Competency).where(Competency.id == fb.competency_id)) if fb.competency_id else None
    return FeedbackResponse(
        id=str(fb.id),
        feedback_id=fb.feedback_id,
        subject_employee_id=str(fb.subject_employee_id),
        author_employee_id=str(fb.author_employee_id),
        subject_name=sub.name,
        author_name=auth.name,
        feedback_type=fb.feedback_type,
        competency_name=comp.name if comp else None,
        rating=fb.rating,
        comments=fb.comments,
        status=fb.status,
        submitted_at=fb.submitted_at,
        created_at=fb.created_at,
        updated_at=fb.updated_at,
    )

