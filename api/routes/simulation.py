from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.strategy_builder import simulate_strategy
from app.simulation.models import SimulationRequest

router = APIRouter(tags=["simulation"])


@router.post("/simulate")
def simulate(request: SimulationRequest, db: Session = Depends(get_db)):
    return simulate_strategy(db, request)
