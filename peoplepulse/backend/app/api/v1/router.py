from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    audit,
    auth,
    check_ins,
    competencies,
    dashboard,
    development_plans,
    employees,
    feedback,
    goals,
    issues,
    review_cycles,
    reviews,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(employees.router)
api_router.include_router(review_cycles.router)
api_router.include_router(goals.router)
api_router.include_router(check_ins.router)
api_router.include_router(competencies.router)
api_router.include_router(feedback.router)
api_router.include_router(reviews.router)
api_router.include_router(development_plans.router)
api_router.include_router(issues.router)
api_router.include_router(audit.router)
api_router.include_router(admin.router)

@api_router.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "peoplepulse-backend", "version": "1.0.0"}

