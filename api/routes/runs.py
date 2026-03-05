from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from app.infrastructure.db.session import get_db
from app.infrastructure.persistence_models.user import User
from app.infrastructure.repositories.simulation_run_repository import (
    SimulationRunRepository,
)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
def list_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SimulationRunRepository(db)
    runs = repo.list_for_user(current_user.id)

    return [
        {
            "run_id": str(r.id),
            "dataset_id": str(r.dataset_id),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            # quick summary for listing
            "roi_percent": r.result_json.get("roi_percent"),
            "final_bankroll": r.result_json.get("final_bankroll"),
            "total_bets": r.result_json.get("total_bets"),
            "max_drawdown_percent": r.result_json.get("max_drawdown_percent"),
        }
        for r in runs
    ]


@router.get("/{run_id}")
def get_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SimulationRunRepository(db)
    r = repo.get_for_user(run_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": str(r.id),
        "dataset_id": str(r.dataset_id),
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "mapping": r.mapping_json,
        "request": r.request_json,
        "result": r.result_json,
    }


@router.delete("/{run_id}")
def delete_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SimulationRunRepository(db)
    r = repo.get_for_user(run_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")

    repo.delete(r)
    return {"status": "deleted", "run_id": str(run_id)}
