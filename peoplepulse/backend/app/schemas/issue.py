from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict

class IssueResolve(BaseModel):
    notes: Optional[str] = None
    resolution_status: str = "resolved"

class IssueResponse(BaseModel):
    id: str
    issue_id: str
    issue_type: str
    entity_type: str
    entity_id: str
    severity: str
    rule_id: str
    explanation: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    detected_at: datetime
    resolution_status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    evidence_refs: Optional[List[Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

