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
    # New preferred field.
    parameters: dict[str, Any]
    # Backward-compatible alias for older consumers.
    params: dict[str, Any]
    run_id: str | None = None
    roi_percent: float | None = None
    final_bankroll: float | None = None
    total_bets: int | None = None
    total_wins: int | None = None
    total_losses: int | None = None
    max_drawdown_percent: float | None = None
    strike_rate_percent: float | None = None
    profit_factor: float | None = None
    average_odds: float | None = None
    total_profit: float | None = None


class DatasetSweepResponse(BaseModel):
    # New analytics-oriented shape.
    parameter_names: list[str]
    row_count: int
    rows: list[SweepVariantResult]
    # Backward-compatible aliases.
    total_variants: int
    results: list[SweepVariantResult]
