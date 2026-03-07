import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from app.infrastructure.db.session import get_db
from app.infrastructure.persistence_models.user import User
from app.infrastructure.repositories.simulation_run_repository import (
    SimulationRunRepository,
)

router = APIRouter(prefix="/runs", tags=["runs"])


def _flatten_bets_to_csv_rows(run_id: str, result_json: dict):
    bets = result_json.get("bets", [])
    rows = []

    for bet_index, bet in enumerate(bets, start=1):
        stake = bet.get("stake")
        combined_odds = bet.get("combined_odds")
        is_win = bet.get("is_win")
        profit = bet.get("profit")
        return_amount = bet.get("return_amount")
        settled_at = bet.get("settled_at")

        legs = bet.get("legs", [])

        for leg_index, leg in enumerate(legs, start=1):
            row = {
                "run_id": run_id,
                "bet_index": bet_index,
                "leg_index": leg_index,
                "stake": stake,
                "combined_odds": combined_odds,
                "is_win": is_win,
                "profit": profit,
                "return_amount": return_amount,
                "settled_at": settled_at,
                "match_id": leg.get("match_id"),
                "kickoff": leg.get("kickoff"),
                "home_team": leg.get("home_team"),
                "away_team": leg.get("away_team"),
                "result": leg.get("result"),
                "selection": leg.get("selection"),
                "odds": leg.get("odds"),
                "implied_prob": leg.get("implied_prob"),
                "model_prob": leg.get("model_prob"),
                "edge": leg.get("edge"),
            }

            for k, v in (leg.get("features") or {}).items():
                row[f"feature__{k}"] = v

            rows.append(row)

    return rows


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


@router.get("/{run_id}/export/bets.csv")
def export_run_bets_csv(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SimulationRunRepository(db)
    r = repo.get_for_user(run_id, current_user.id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")

    rows = _flatten_bets_to_csv_rows(str(r.id), r.result_json)

    base_fieldnames = [
        "run_id",
        "bet_index",
        "leg_index",
        "stake",
        "combined_odds",
        "is_win",
        "profit",
        "return_amount",
        "settled_at",
        "match_id",
        "kickoff",
        "home_team",
        "away_team",
        "result",
        "selection",
        "odds",
        "implied_prob",
        "model_prob",
        "edge",
    ]

    feature_fieldnames = sorted(
        {k for row in rows for k in row.keys() if k.startswith("feature__")}
    )

    fieldnames = base_fieldnames + feature_fieldnames

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    filename = f"run_{r.id}_bets.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
