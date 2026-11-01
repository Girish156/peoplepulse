from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class DevelopmentPlanActionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None

class DevelopmentPlanActionResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: str
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DevelopmentPlanCreate(BaseModel):
    plan_id: Optional[str] = None
    employee_id: str
    review_id: Optional[str] = None
    objectives: str
    actions: Optional[List[DevelopmentPlanActionCreate]] = []

class DevelopmentPlanResponse(BaseModel):
    id: str
    plan_id: str
    employee_id: str
    employee_name: Optional[str] = None
    review_id: Optional[str] = None
    objectives: str
    status: str
    approver_id: Optional[str] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    completion_date: Optional[date] = None
    actions: List[DevelopmentPlanActionResponse] = []
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

