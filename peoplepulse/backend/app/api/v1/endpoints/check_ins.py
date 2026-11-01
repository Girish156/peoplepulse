from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.db.session import get_db
from app.models.check_in import CheckIn, Evidence
from app.models.employee import Employee
from app.models.goal import Goal
from app.schemas.check_in import CheckInResponse, EvidenceResponse

router = APIRouter(prefix="/check-ins", tags=["Check-ins"])

@router.get("", response_model=List[CheckInResponse])
def list_check_ins(
    skip: int = 0,
    limit: int = 50,
    employee_id: Optional[str] = None,
    goal_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(CheckIn)
    if employee_id:
        emp = db.scalar(select(Employee).where(or_(Employee.id == employee_id, Employee.employee_id == employee_id)))
        if emp:
            stmt = stmt.where(CheckIn.employee_id == emp.id)
    if goal_id:
        goal = db.scalar(select(Goal).where(or_(Goal.id == goal_id, Goal.goal_id == goal_id)))
        if goal:
            stmt = stmt.where(CheckIn.goal_id == goal.id)

    stmt = stmt.order_by(CheckIn.check_in_date.desc()).offset(skip).limit(limit)
    check_ins = db.scalars(stmt).all()

    emp_map = {e.id: e for e in db.scalars(select(Employee)).all()}
    goal_map = {g.id: g for g in db.scalars(select(Goal)).all()}

    results = []
    for ci in check_ins:
        emp = emp_map.get(ci.employee_id)
        goal = goal_map.get(ci.goal_id)
        evidence_records = db.scalars(select(Evidence).where(Evidence.check_in_id == ci.id)).all()
        results.append(
            CheckInResponse(
                id=str(ci.id),
                check_in_id=ci.check_in_id,
                employee_id=str(ci.employee_id),
                goal_id=str(ci.goal_id),
                cycle_id=str(ci.cycle_id),
                employee_name=emp.name if emp else None,
                employee_business_id=emp.employee_id if emp else None,
                goal_title=goal.title if goal else None,
                check_in_date=ci.check_in_date,
                notes=ci.notes,
                progress_snapshot=ci.progress_snapshot,
                status=ci.status,
                evidence=[EvidenceResponse.model_validate(e) for e in evidence_records],
                created_at=ci.created_at,
            )
        )
    return results

