from typing import Literal

from pydantic import BaseModel


class SimulationRequest(BaseModel):
    league: str
    season: str
    # selection: Literal["H", "D", "A"]

    staking_method: Literal["fixed", "percent", "kelly"]

    fixed_stake: float | None = None
    percent_stake: float | None = None
    kelly_fraction: float | None = None  # e.g. 0.5 for half Kelly

    starting_bankroll: float
    multiple_legs: int = 1  # 1 = singles, 2 = double, etc.

    min_odds: float | None = None
