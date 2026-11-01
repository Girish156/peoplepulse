from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.competency import Competency
from app.schemas.competency import CompetencyResponse

router = APIRouter(prefix="/competencies", tags=["Competencies"])

@router.get("", response_model=List[CompetencyResponse])
def list_competencies(db: Session = Depends(get_db)):
    comps = db.scalars(select(Competency).order_by(Competency.competency_id)).all()
    return [
        CompetencyResponse(
            id=str(c.id),
            competency_id=c.competency_id,
            name=c.name,
            description=c.description,
            rating_scale=c.rating_scale,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comps
    ]

