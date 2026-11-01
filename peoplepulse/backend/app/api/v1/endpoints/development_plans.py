from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.db.session import get_db
from app.models.development_plan import DevelopmentPlan, DevelopmentPlanAction
from app.models.employee import Employee
from app.schemas.development_plan import DevelopmentPlanCreate, DevelopmentPlanResponse, DevelopmentPlanActionResponse
from app.services.audit import create_audit_event

router = APIRouter(prefix="/development-plans", tags=["Development Plans"])

@router.get("", response_model=List[DevelopmentPlanResponse])
def list_development_plans(
    skip: int = 0,
    limit: int = 50,
    employee_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(DevelopmentPlan)
    if employee_id:
        emp = db.scalar(select(Employee).where(or_(Employee.id == employee_id, Employee.employee_id == employee_id)))
        if emp:
            stmt = stmt.where(DevelopmentPlan.employee_id == emp.id)

    stmt = stmt.order_by(DevelopmentPlan.created_at.desc()).offset(skip).limit(limit)
    plans = db.scalars(stmt).all()

    emp_map = {e.id: e for e in db.scalars(select(Employee)).all()}

    results = []
    for p in plans:
        emp = emp_map.get(p.employee_id)
        approver = emp_map.get(p.approver_id) if p.approver_id else None
        actions = db.scalars(select(DevelopmentPlanAction).where(DevelopmentPlanAction.plan_id == p.id)).all()
        results.append(
            DevelopmentPlanResponse(
                id=str(p.id),
                plan_id=p.plan_id,
                employee_id=str(p.employee_id),
                employee_name=emp.name if emp else None,
                review_id=str(p.review_id) if p.review_id else None,
                objectives=p.objectives,
                status=p.status,
                approver_id=str(p.approver_id) if p.approver_id else None,
                approver_name=approver.name if approver else None,
                approved_at=p.approved_at,
                completion_date=p.completion_date,
                version=p.version,
                actions=[DevelopmentPlanActionResponse.model_validate(a) for a in actions],
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return results

@router.post("", response_model=DevelopmentPlanResponse, status_code=status.HTTP_201_CREATED)
def create_development_plan(payload: DevelopmentPlanCreate, db: Session = Depends(get_db)):
    emp = db.scalar(select(Employee).where(or_(Employee.id == payload.employee_id, Employee.employee_id == payload.employee_id)))
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    p_id = payload.plan_id
    if not p_id:
        count = db.scalar(select(func.count(DevelopmentPlan.id)).where(DevelopmentPlan.employee_id == emp.id)) or 0
        p_id = f"DEV-{emp.employee_id}-{count + 1:03d}"

    plan = DevelopmentPlan(
        plan_id=p_id,
        employee_id=emp.id,
        review_id=payload.review_id,
        objectives=payload.objectives,
        status="active",
        version=1,
    )
    db.add(plan)
    db.flush()

    action_responses = []
    for act_in in payload.actions or []:
        act = DevelopmentPlanAction(
            plan_id=plan.id,
            title=act_in.title,
            description=act_in.description,
            due_date=act_in.due_date,
            status="in_progress",
        )
        db.add(act)
        db.flush()
        action_responses.append(DevelopmentPlanActionResponse.model_validate(act))

    create_audit_event(
        db=db,
        actor_employee_id=str(emp.id),
        actor_role="employee",
        action="development_plan.created",
        entity_type="development_plan",
        entity_id=plan.plan_id,
        after_state={"plan_id": plan.plan_id, "objectives": plan.objectives},
        reason="Plan initialized",
    )

    db.commit()
    db.refresh(plan)

    return DevelopmentPlanResponse(
        id=str(plan.id),
        plan_id=plan.plan_id,
        employee_id=str(plan.employee_id),
        employee_name=emp.name,
        review_id=str(plan.review_id) if plan.review_id else None,
        objectives=plan.objectives,
        status=plan.status,
        approver_id=None,
        approver_name=None,
        approved_at=None,
        completion_date=None,
        actions=action_responses,
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )

@router.post("/{plan_id}/approve", response_model=DevelopmentPlanResponse)
def approve_development_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.scalar(select(DevelopmentPlan).where(or_(DevelopmentPlan.id == plan_id, DevelopmentPlan.plan_id == plan_id)))
    if not plan:
        raise HTTPException(status_code=404, detail="Development plan not found")

    plan.status = "completed"
    plan.approved_at = datetime.now(timezone.utc)
    plan.version += 1

    create_audit_event(
        db=db,
        actor_employee_id=None,
        actor_role="manager",
        action="development_plan.approved",
        entity_type="development_plan",
        entity_id=plan.plan_id,
        after_state={"plan_id": plan.plan_id, "status": plan.status},
        reason="Development plan approved",
    )

    db.commit()
    db.refresh(plan)

    emp = db.scalar(select(Employee).where(Employee.id == plan.employee_id))
    actions = db.scalars(select(DevelopmentPlanAction).where(DevelopmentPlanAction.plan_id == plan.id)).all()
    return DevelopmentPlanResponse(
        id=str(plan.id),
        plan_id=plan.plan_id,
        employee_id=str(plan.employee_id),
        employee_name=emp.name if emp else None,
        review_id=str(plan.review_id) if plan.review_id else None,
        objectives=plan.objectives,
        status=plan.status,
        approver_id=None,
        approver_name="Approving Manager",
        approved_at=plan.approved_at,
        completion_date=plan.completion_date,
        actions=[DevelopmentPlanActionResponse.model_validate(a) for a in actions],
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )

