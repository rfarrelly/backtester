from typing import Literal

from pydantic import BaseModel, model_validator


class SimulationRequest(BaseModel):
    league: str
    season: str
    strategy_type: Literal["home", "edge", "rules"]

    selection: Literal["H", "D", "A"] | None = None
    rule_expression: str | None = None

    staking_method: Literal["fixed", "percent", "kelly"]

    fixed_stake: float | None = None
    percent_stake: float | None = None
    kelly_fraction: float | None = None  # e.g. 0.5 for half Kelly

    starting_bankroll: float
    multiple_legs: int = 1  # 1 = singles, 2 = double, etc.

    min_odds: float | None = None
    min_edge: float | None = None

    @model_validator(mode="after")
    def validate_request(self):
        # Strategy requirements
        if self.strategy_type == "edge":
            if self.selection is None:
                raise ValueError("selection is required for strategy_type='edge'")
            if self.min_edge is None:
                raise ValueError("min_edge is required for strategy_type='edge'")

        # Staking requirements
        if self.staking_method == "fixed":
            if self.fixed_stake is None:
                raise ValueError("fixed_stake is required for staking_method='fixed'")

        if self.staking_method == "percent":
            if self.percent_stake is None:
                raise ValueError(
                    "percent_stake is required for staking_method='percent'"
                )
            if not (0 < self.percent_stake <= 1):
                raise ValueError("percent_stake must be in (0, 1]")

        if self.staking_method == "kelly":
            if self.kelly_fraction is None:
                raise ValueError(
                    "kelly_fraction is required for staking_method='kelly'"
                )
            if not (0 < self.kelly_fraction <= 1):
                raise ValueError("kelly_fraction must be in (0, 1]")

        # General sanity
        if self.starting_bankroll <= 0:
            raise ValueError("starting_bankroll must be > 0")
        if self.multiple_legs < 1:
            raise ValueError("multiple_legs must be >= 1")
        if self.min_odds is not None and self.min_odds <= 1:
            raise ValueError("min_odds must be > 1 (decimal odds)")

        return self
