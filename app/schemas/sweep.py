from typing import Any

from pydantic import BaseModel

from app.application.dataset_mapping import DatasetMapping
from app.domain.simulation.models import SimulationRequest


class DatasetSweepRequest(BaseModel):
    mapping: DatasetMapping
    base_request: SimulationRequest
    grid: dict[str, list[Any]]
    persist_runs: bool = True


class SweepVariantResult(BaseModel):
    params: dict[str, Any]
    run_id: str | None = None
    roi_percent: float
    final_bankroll: float
    total_bets: int
    max_drawdown_percent: float | None = None
    strike_rate_percent: float | None = None
    profit_factor: float | None = None
    average_odds: float | None = None
    total_profit: float | None = None


class DatasetSweepResponse(BaseModel):
    total_variants: int
    results: list[SweepVariantResult]
