from typing import Any, Dict, List
from pydantic import BaseModel

class DepartmentCount(BaseModel):
    department: str
    count: int

class RecentAuditSummary(BaseModel):
    event_id: str
    action: str
    entity_type: str
    entity_id: str
    actor_role: str | None = None
    reason: str | None = None
    created_at: str | None = None

class DashboardMetricsResponse(BaseModel):
    total_employees: int
    active_goals: int
    avg_goal_progress: float
    check_in_completion_rate: float
    total_check_ins: int
    total_reviews: int
    completed_reviews: int
    review_completion_rate: float
    outstanding_feedback: int
    unresolved_issues: int
    issue_severities: Dict[str, int]
    department_breakdown: List[DepartmentCount]
    recent_audit_events: List[RecentAuditSummary]

