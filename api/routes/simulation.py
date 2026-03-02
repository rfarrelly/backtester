from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.simulation_service import SimulationService
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.rules import RuleCompileError
from app.infrastructure.db.session import get_db

router = APIRouter(tags=["simulation"])


@router.post("/simulate")
def simulate(request: SimulationRequest, db: Session = Depends(get_db)):
    service = SimulationService(db)
    try:
        return service.run(request)
    except RuleCompileError as e:
        raise HTTPException(status_code=400, detail=str(e))
