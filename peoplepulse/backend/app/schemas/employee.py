from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class EmployeeBase(BaseModel):
    employee_id: str
    name: str
    email: EmailStr
    department: str
    job_title: str
    employment_status: str = "active"
    hire_date: date
    termination_date: Optional[date] = None

class EmployeeCreate(BaseModel):
    employee_id: Optional[str] = None
    name: str
    email: EmailStr
    department: str
    job_title: str
    employment_status: str = "active"
    manager_employee_id: Optional[str] = None
    hire_date: date
    termination_date: Optional[date] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    employment_status: Optional[str] = None
    manager_employee_id: Optional[str] = None
    termination_date: Optional[date] = None

class EmployeeResponse(EmployeeBase):
    id: str
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    manager_employee_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

