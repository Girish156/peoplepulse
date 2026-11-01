from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.db.session import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate
from app.services.audit import create_audit_event

router = APIRouter(prefix="/employees", tags=["Employees"])

@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    department: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Employee)
    if department:
        stmt = stmt.where(Employee.department == department)
    if status_filter and isinstance(status_filter, str):
        stmt = stmt.where(Employee.employment_status == status_filter)
    if search:
        term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Employee.name.ilike(term),
                Employee.employee_id.ilike(term),
                Employee.email.ilike(term),
                Employee.job_title.ilike(term),
            )
        )
    stmt = stmt.order_by(Employee.employee_id).offset(skip).limit(limit)
    employees = db.scalars(stmt).all()
    
    # Enrich with manager info
    results = []
    emp_map = {e.id: e for e in db.scalars(select(Employee)).all()}
    for e in employees:
        mgr = emp_map.get(e.manager_id) if e.manager_id else None
        res = EmployeeResponse(
            id=str(e.id),
            employee_id=e.employee_id,
            name=e.name,
            email=e.email,
            department=e.department,
            job_title=e.job_title,
            employment_status=e.employment_status,
            manager_id=str(e.manager_id) if e.manager_id else None,
            manager_name=mgr.name if mgr else None,
            manager_employee_id=mgr.employee_id if mgr else None,
            hire_date=e.hire_date,
            termination_date=e.termination_date,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        results.append(res)
    return results

@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: str, db: Session = Depends(get_db)):
    # Look up by UUID or business ID
    e = db.scalar(
        select(Employee).where(
            or_(Employee.id == emp_id, Employee.employee_id == emp_id)
        )
    )
    if not e:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    mgr = db.scalar(select(Employee).where(Employee.id == e.manager_id)) if e.manager_id else None
    return EmployeeResponse(
        id=str(e.id),
        employee_id=e.employee_id,
        name=e.name,
        email=e.email,
        department=e.department,
        job_title=e.job_title,
        employment_status=e.employment_status,
        manager_id=str(e.manager_id) if e.manager_id else None,
        manager_name=mgr.name if mgr else None,
        manager_employee_id=mgr.employee_id if mgr else None,
        hire_date=e.hire_date,
        termination_date=e.termination_date,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    # Check duplicate email
    if db.scalar(select(Employee).where(Employee.email == payload.email)):
        raise HTTPException(status_code=409, detail="An employee with this email already exists")

    # Generate employee_id if not given
    emp_id = payload.employee_id
    if not emp_id:
        count = db.scalar(select(func.count(Employee.id))) or 0
        emp_id = f"EMP-{count + 1:06d}"

    mgr_id = None
    if payload.manager_employee_id:
        mgr = db.scalar(select(Employee).where(Employee.employee_id == payload.manager_employee_id))
        if mgr:
            mgr_id = mgr.id

    e = Employee(
        employee_id=emp_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
        job_title=payload.job_title,
        employment_status=payload.employment_status,
        manager_id=mgr_id,
        hire_date=payload.hire_date,
        termination_date=payload.termination_date,
    )
    db.add(e)
    db.flush()

    create_audit_event(
        db=db,
        actor_employee_id=None,
        actor_role="admin",
        action="employee.created",
        entity_type="employee",
        entity_id=e.employee_id,
        after_state={"employee_id": e.employee_id, "name": e.name, "department": e.department},
        reason="Employee record creation",
    )
    db.commit()
    db.refresh(e)

    mgr = db.scalar(select(Employee).where(Employee.id == e.manager_id)) if e.manager_id else None
    return EmployeeResponse(
        id=str(e.id),
        employee_id=e.employee_id,
        name=e.name,
        email=e.email,
        department=e.department,
        job_title=e.job_title,
        employment_status=e.employment_status,
        manager_id=str(e.manager_id) if e.manager_id else None,
        manager_name=mgr.name if mgr else None,
        manager_employee_id=mgr.employee_id if mgr else None,
        hire_date=e.hire_date,
        termination_date=e.termination_date,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )
