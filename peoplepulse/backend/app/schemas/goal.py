from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.key_result import KeyResultCreate, KeyResultResponse

class GoalBase(BaseModel):
    goal_id: str
    title: str
    description: Optional[str] = None
    status: str = "draft"
    weight: float = 1.0
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    version: int = 1
    rationale: Optional[str] = None

class GoalCreate(BaseModel):
    goal_id: Optional[str] = None
    employee_employee_id: str
    cycle_cycle_id: str
    title: str
    description: Optional[str] = None
    status: Optional[str] = "draft"
    weight: Optional[float] = 1.0
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    rationale: Optional[str] = None
    key_results: Optional[List[KeyResultCreate]] = []

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    weight: Optional[float] = None
    due_date: Optional[date] = None
    rationale: Optional[str] = None

class GoalResponse(GoalBase):
    id: str
    employee_id: str
    cycle_id: str
    employee_name: Optional[str] = None
    employee_business_id: Optional[str] = None
    cycle_business_id: Optional[str] = None
    key_results: List[KeyResultResponse] = []
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

