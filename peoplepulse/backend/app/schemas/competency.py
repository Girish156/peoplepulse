from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class CompetencyBase(BaseModel):
    competency_id: str
    name: str
    description: str
    rating_scale: int = 5
    is_active: bool = True

class CompetencyCreate(CompetencyBase):
    pass

class CompetencyResponse(CompetencyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

