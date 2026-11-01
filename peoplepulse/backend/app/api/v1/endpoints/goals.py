from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.db.session import get_db
from app.models.goal import Goal, GoalVersion
from app.models.key_result import KeyResult
from app.models.employee import Employee
from app.models.review_cycle import ReviewCycle
from app.models.check_in import CheckIn, Evidence
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.schemas.key_result import KeyResultResponse
from app.schemas.check_in import CheckInCreate, CheckInResponse, EvidenceResponse
from app.services.progress import calculate_goal_progress, calculate_key_result_progress
from app.services.lifecycle import can_mutate_cycle
from app.services.audit import create_audit_event

router = APIRouter(prefix="/goals", tags=["Goals"])

def build_goal_response(g: Goal, db: Session) -> GoalResponse:
    krs = db.scalars(select(KeyResult).where(KeyResult.goal_id == g.id)).all()
    kr_dicts = []
    kr_responses = []
    
    for kr in krs:
        actual_val = float(kr.actual) if kr.actual is not None else None
        target_val = float(kr.target)
        base_val = float(kr.baseline or 0.0)
        scale_val = float(kr.allowed_progress_scale or 1.0)
        
        kr_res = calculate_key_result_progress(
            baseline=base_val,
            actual=actual_val,
            target=target_val,
            metric_type=kr.metric_type,
            allowed_scale=scale_val,
        )
        pct = (
            round(kr_res["capped_progress"] * 100, 1)
            if kr_res["capped_progress"] is not None
            else None
        )
        kr_responses.append(
            KeyResultResponse(
                id=str(kr.id),
                key_result_id=kr.key_result_id,
                goal_id=str(g.id),
                title=kr.title,
                metric_type=kr.metric_type,
                unit=kr.unit,
                baseline=base_val,
                target=target_val,
                actual=actual_val,
                weight=float(kr.weight or 1.0),
                allowed_progress_scale=scale_val,
                progress_percentage=pct,
                version=kr.version,
                created_at=kr.created_at,
                updated_at=kr.updated_at,
            )
        )
        kr_dicts.append({
            "baseline": base_val,
            "actual": actual_val,
            "target": target_val,
            "weight": float(kr.weight or 1.0),
            "metric_type": kr.metric_type,
            "allowed_scale": scale_val,
        })
        
    goal_calc = calculate_goal_progress(kr_dicts)
    overall_pct = round(goal_calc["weighted_progress"] * 100, 1)

    emp = db.scalar(select(Employee).where(Employee.id == g.employee_id))
    cycle = db.scalar(select(ReviewCycle).where(ReviewCycle.id == g.cycle_id))

    return GoalResponse(
        id=str(g.id),
        goal_id=g.goal_id,
        employee_id=str(g.employee_id),
        cycle_id=str(g.cycle_id),
        employee_name=emp.name if emp else None,
        employee_business_id=emp.employee_id if emp else None,
        cycle_business_id=cycle.cycle_id if cycle else None,
        title=g.title,
        description=g.description,
        status=g.status,
        weight=float(g.weight or 1.0),
        start_date=g.start_date,
        due_date=g.due_date,
        version=g.version,
        rationale=g.rationale,
        key_results=kr_responses,
        progress_percentage=overall_pct,
        created_at=g.created_at,
        updated_at=g.updated_at,
    )

@router.get("", response_model=List[GoalResponse])
def list_goals(
    skip: int = 0,
    limit: int = 50,
    employee_id: Optional[str] = None,
    cycle_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Goal)
    if employee_id:
        emp = db.scalar(
            select(Employee).where(
                or_(Employee.id == employee_id, Employee.employee_id == employee_id)
            )
        )
        if emp:
            stmt = stmt.where(Goal.employee_id == emp.id)
    if cycle_id:
        cycle = db.scalar(
            select(ReviewCycle).where(
                or_(ReviewCycle.id == cycle_id, ReviewCycle.cycle_id == cycle_id)
            )
        )
        if cycle:
            stmt = stmt.where(Goal.cycle_id == cycle.id)
    if status_filter and isinstance(status_filter, str):
        stmt = stmt.where(Goal.status == status_filter)

    stmt = stmt.order_by(Goal.created_at.desc()).offset(skip).limit(limit)
    goals = db.scalars(stmt).all()
    return [build_goal_response(g, db) for g in goals]

@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: str, db: Session = Depends(get_db)):
    g = db.scalar(
        select(Goal).where(or_(Goal.id == goal_id, Goal.goal_id == goal_id))
    )
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    return build_goal_response(g, db)

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    emp = db.scalar(
        select(Employee).where(
            or_(Employee.id == payload.employee_employee_id, Employee.employee_id == payload.employee_employee_id)
        )
    )
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {payload.employee_employee_id} not found")

    cycle = db.scalar(
        select(ReviewCycle).where(
            or_(ReviewCycle.id == payload.cycle_cycle_id, ReviewCycle.cycle_id == payload.cycle_cycle_id)
        )
    )
    if not cycle:
        raise HTTPException(status_code=404, detail=f"Cycle {payload.cycle_cycle_id} not found")

    if not can_mutate_cycle(cycle):
        raise HTTPException(status_code=409, detail=f"Cannot add goals to cycle in status '{cycle.status}'")

    gid = payload.goal_id
    if not gid:
        existing_count = db.scalar(select(func.count(Goal.id)).where(Goal.employee_id == emp.id)) or 0
        gid = f"GOAL-{emp.employee_id}-{existing_count + 1:03d}"

    goal = Goal(
        goal_id=gid,
        employee_id=emp.id,
        cycle_id=cycle.id,
        title=payload.title,
        description=payload.description,
        status=payload.status or "active",
        weight=payload.weight or 1.0,
        start_date=payload.start_date,
        due_date=payload.due_date,
        version=1,
        rationale=payload.rationale,
    )
    db.add(goal)
    db.flush()

    # Add Key Results if provided
    for idx, kr_in in enumerate(payload.key_results or []):
        kr_id = kr_in.key_result_id or f"KR-{gid}-{idx+1:02d}"
        kr = KeyResult(
            key_result_id=kr_id,
            goal_id=goal.id,
            title=kr_in.title,
            metric_type=kr_in.metric_type,
            unit=kr_in.unit,
            baseline=kr_in.baseline,
            target=kr_in.target,
            actual=kr_in.actual,
            weight=kr_in.weight,
            allowed_progress_scale=kr_in.allowed_progress_scale,
            version=1,
        )
        db.add(kr)

    create_audit_event(
        db=db,
        actor_employee_id=str(emp.id),
        actor_role="employee",
        action="goal.created",
        entity_type="goal",
        entity_id=goal.goal_id,
        after_state={"goal_id": goal.goal_id, "title": goal.title},
        reason="Goal initialized",
    )

    db.commit()
    db.refresh(goal)
    return build_goal_response(goal, db)

@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: str, payload: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.scalar(select(Goal).where(or_(Goal.id == goal_id, Goal.goal_id == goal_id)))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    cycle = db.scalar(select(ReviewCycle).where(ReviewCycle.id == goal.cycle_id))
    if cycle and not can_mutate_cycle(cycle):
        raise HTTPException(status_code=409, detail=f"Cannot modify goals in a {cycle.status} cycle without authorization")

    before = {"title": goal.title, "status": goal.status, "weight": float(goal.weight or 1.0)}

    if payload.title is not None:
        goal.title = payload.title
    if payload.description is not None:
        goal.description = payload.description
    if payload.status is not None:
        goal.status = payload.status
    if payload.weight is not None:
        goal.weight = payload.weight
    if payload.due_date is not None:
        goal.due_date = payload.due_date
    if payload.rationale is not None:
        goal.rationale = payload.rationale

    goal.version += 1

    create_audit_event(
        db=db,
        actor_employee_id=str(goal.employee_id),
        actor_role="employee",
        action="goal.updated",
        entity_type="goal",
        entity_id=goal.goal_id,
        before_state=before,
        after_state={"title": goal.title, "status": goal.status, "weight": float(goal.weight or 1.0)},
        reason=payload.rationale or "Goal updated",
    )

    db.commit()
    db.refresh(goal)
    return build_goal_response(goal, db)

@router.post("/{goal_id}/check-ins", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def create_goal_check_in(
    goal_id: str,
    payload: CheckInCreate,
    db: Session = Depends(get_db),
):
    goal = db.scalar(select(Goal).where(or_(Goal.id == goal_id, Goal.goal_id == goal_id)))
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    cycle = db.scalar(select(ReviewCycle).where(ReviewCycle.id == goal.cycle_id))
    if cycle and not can_mutate_cycle(cycle):
        raise HTTPException(status_code=409, detail=f"Cannot record check-in for a {cycle.status} cycle")

    emp = db.scalar(
        select(Employee).where(
            or_(Employee.id == payload.employee_employee_id, Employee.employee_id == payload.employee_employee_id)
        )
    )
    if not emp:
        raise HTTPException(status_code=404, detail=f"Employee {payload.employee_employee_id} not found")

    # Generate check-in ID if not given
    ci_id = payload.check_in_id
    if not ci_id:
        ci_count = db.scalar(select(func.count(CheckIn.id)).where(CheckIn.goal_id == goal.id)) or 0
        date_str = payload.check_in_date.strftime("%Y%m%d")
        ci_id = f"CHK-{emp.employee_id}-{date_str}-{ci_count+1:03d}"

    ci = CheckIn(
        check_in_id=ci_id,
        employee_id=emp.id,
        goal_id=goal.id,
        cycle_id=goal.cycle_id,
        check_in_date=payload.check_in_date,
        notes=payload.notes,
        progress_snapshot=payload.progress_snapshot,
        status="submitted",
    )
    db.add(ci)
    db.flush()

    # Update actual values on key results if provided in progress_snapshot
    if payload.progress_snapshot:
        krs = db.scalars(select(KeyResult).where(KeyResult.goal_id == goal.id)).all()
        for kr in krs:
            # check key_result_id or kr.id
            if kr.key_result_id in payload.progress_snapshot:
                kr.actual = float(payload.progress_snapshot[kr.key_result_id])
                kr.version += 1
            elif str(kr.id) in payload.progress_snapshot:
                kr.actual = float(payload.progress_snapshot[str(kr.id)])
                kr.version += 1

    # Attach evidence if provided
    evidence_resp = []
    for idx, ev_in in enumerate(payload.evidence or []):
        ev_id = f"EVD-{ci.check_in_id[-6:]}-{idx+1:02d}"
        ev = Evidence(
            evidence_id=ev_id,
            check_in_id=ci.id,
            title=ev_in.title,
            description=ev_in.description,
            url=ev_in.url,
            evidence_type=ev_in.evidence_type,
        )
        db.add(ev)
        db.flush()
        evidence_resp.append(EvidenceResponse.model_validate(ev))

    create_audit_event(
        db=db,
        actor_employee_id=str(emp.id),
        actor_role="employee",
        action="check_in.submitted",
        entity_type="check_in",
        entity_id=ci.check_in_id,
        after_state={"check_in_id": ci.check_in_id, "goal_id": goal.goal_id, "notes": ci.notes},
        reason="Check-in submission",
    )

    db.commit()
    db.refresh(ci)

    return CheckInResponse(
        id=str(ci.id),
        check_in_id=ci.check_in_id,
        employee_id=str(ci.employee_id),
        goal_id=str(ci.goal_id),
        cycle_id=str(ci.cycle_id),
        employee_name=emp.name,
        employee_business_id=emp.employee_id,
        goal_title=goal.title,
        check_in_date=ci.check_in_date,
        notes=ci.notes,
        progress_snapshot=ci.progress_snapshot,
        status=ci.status,
        evidence=evidence_resp,
        created_at=ci.created_at,
    )
