from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domain.simulation.models import SimulationRequest
from app.infrastructure.db.session import get_db
from app.services.strategy_builder import simulate_strategy

router = APIRouter(tags=["simulation"])


@router.post("/simulate")
def simulate(request: SimulationRequest, db: Session = Depends(get_db)):
    return simulate_strategy(db, request)
