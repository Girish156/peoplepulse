from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.dashboard import DashboardMetricsResponse
from app.services.metrics import get_dashboard_metrics

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardMetricsResponse)
def read_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Returns real database-computed KPIs, rates, and distributions.
    """
    return get_dashboard_metrics(db)

