from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ReviewParticipantResponse(BaseModel):
    id: str
    participant_employee_id: str
    participant_name: Optional[str] = None
    role: str
    is_required: bool
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReviewBase(BaseModel):
    review_id: str
    status: str = "pending"
    goal_score: Optional[float] = None
    feedback_score: Optional[float] = None
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    version: int = 1

class ReviewCreate(BaseModel):
    review_id: Optional[str] = None
    employee_id: str
    cycle_id: str
    reviewer_id: str
    summary: Optional[str] = None

class ReviewSubmit(BaseModel):
    summary: Optional[str] = None
    goal_score: Optional[float] = None
    feedback_score: Optional[float] = None
    overall_score: Optional[float] = None

class ReviewResponse(ReviewBase):
    id: str
    employee_id: str
    cycle_id: str
    reviewer_id: str
    employee_name: Optional[str] = None
    reviewer_name: Optional[str] = None
    cycle_name: Optional[str] = None
    participants: List[ReviewParticipantResponse] = []
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

