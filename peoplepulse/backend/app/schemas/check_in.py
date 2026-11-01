from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class EvidenceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    evidence_type: str = "note"

class EvidenceResponse(BaseModel):
    id: str
    evidence_id: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    evidence_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CheckInCreate(BaseModel):
    check_in_id: Optional[str] = None
    employee_employee_id: str
    goal_goal_id: str
    check_in_date: date
    notes: Optional[str] = None
    progress_snapshot: Optional[Dict[str, float]] = None
    evidence: Optional[List[EvidenceCreate]] = []

class CheckInResponse(BaseModel):
    id: str
    check_in_id: str
    employee_id: str
    goal_id: str
    cycle_id: str
    employee_name: Optional[str] = None
    employee_business_id: Optional[str] = None
    goal_title: Optional[str] = None
    check_in_date: date
    notes: Optional[str] = None
    progress_snapshot: Optional[Dict[str, Any]] = None
    status: str
    evidence: List[EvidenceResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

