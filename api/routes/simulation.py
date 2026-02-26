from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.simulation_service import SimulationService
from app.domain.simulation.models import SimulationRequest
from app.infrastructure.db.session import get_db

router = APIRouter(tags=["simulation"])


@router.post("/simulate")
def simulate(request: SimulationRequest, db: Session = Depends(get_db)):
    service = SimulationService(db)
    return service.run(request)
