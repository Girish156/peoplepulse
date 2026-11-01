from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class FeedbackBase(BaseModel):
    feedback_id: str
    feedback_type: str = "peer"
    rating: Optional[int] = Field(None, ge=1, le=5)
    comments: str
    status: str = "submitted"

class FeedbackCreate(BaseModel):
    feedback_id: Optional[str] = None
    subject_employee_id: str
    author_employee_id: str
    review_id: Optional[str] = None
    feedback_type: str = "peer"
    competency_id: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comments: str

class FeedbackResponse(FeedbackBase):
    id: str
    subject_employee_id: str
    author_employee_id: str
    subject_name: Optional[str] = None
    author_name: Optional[str] = None
    competency_name: Optional[str] = None
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

