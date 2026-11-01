from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ReviewCycleBase(BaseModel):
    cycle_id: str
    name: str
    start_date: date
    end_date: date
    status: str = "draft"
    version: int = 1

class ReviewCycleCreate(BaseModel):
    cycle_id: str
    name: str
    start_date: date
    end_date: date
    status: Optional[str] = "draft"

class ReviewCycleTransition(BaseModel):
    new_status: str
    reason: Optional[str] = None

class ReviewCycleResponse(ReviewCycleBase):
    id: str
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

