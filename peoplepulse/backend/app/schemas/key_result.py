from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class KeyResultBase(BaseModel):
    key_result_id: str
    title: str
    metric_type: str = "percentage"
    unit: Optional[str] = "%"
    baseline: float = 0.0
    target: float
    actual: Optional[float] = None
    weight: float = 1.0
    allowed_progress_scale: float = 1.0
    version: int = 1

class KeyResultCreate(BaseModel):
    key_result_id: Optional[str] = None
    title: str
    metric_type: str = "percentage"
    unit: Optional[str] = "%"
    baseline: float = 0.0
    target: float
    actual: Optional[float] = None
    weight: float = 1.0
    allowed_progress_scale: float = 1.0

class KeyResultUpdate(BaseModel):
    title: Optional[str] = None
    actual: Optional[float] = None
    weight: Optional[float] = None
    allowed_progress_scale: Optional[float] = None

class KeyResultResponse(KeyResultBase):
    id: str
    goal_id: str
    progress_percentage: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

