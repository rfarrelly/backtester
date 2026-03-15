from typing import Literal

from pydantic import BaseModel, model_validator


class SimulationRequest(BaseModel):
    # Dataset filtering
    league: str | None = None
    leagues: list[str] | None = None
    season: str

    # Strategy model
    # Kept temporarily for compatibility, but the application now
    # always uses rule-based strategy construction internally.
    strategy_type: Literal["home", "edge", "rules"] = "rules"
    selection: Literal["H", "D", "A"] | None = None
    rule_expression: str | None = None

    # Staking
    staking_method: Literal["fixed", "percent", "kelly"]
    fixed_stake: float | None = None
    percent_stake: float | None = None
    kelly_fraction: float | None = None

    # Bankroll / bet construction
    starting_bankroll: float
    multiple_legs: int = 1

    # Optional filters
    min_odds: float | None = None

    # Walk-forward
    walk_forward: bool = False
    train_window_matches: int | None = None
    test_window_matches: int | None = None
    step_matches: int | None = None

    # Calendar period mode
    period_mode: Literal["none", "custom_day_groups"] = "none"
    custom_periods: dict[str, list[int]] | None = None
    reset_bankroll_each_period: bool = False

    # Ranking / candidate selection
    max_candidates_per_period: int | None = None
    rank_by: str | None = None
    rank_order: Literal["asc", "desc"] = "asc"
    require_full_candidate_count: bool = False

    @model_validator(mode="after")
    def validate_request(self):
        if not self.season or not self.season.strip():
            raise ValueError("season is required")

        if self.selection is None:
            raise ValueError("selection is required")

        if self.starting_bankroll <= 0:
            raise ValueError("starting_bankroll must be positive")

        if self.multiple_legs <= 0:
            raise ValueError("multiple_legs must be positive")

        if self.staking_method == "fixed":
            if self.fixed_stake is None or self.fixed_stake <= 0:
                raise ValueError(
                    "fixed_stake must be provided and > 0 for fixed staking"
                )

        elif self.staking_method == "percent":
            if self.percent_stake is None or self.percent_stake <= 0:
                raise ValueError(
                    "percent_stake must be provided and > 0 for percent staking"
                )

        elif self.staking_method == "kelly":
            if self.kelly_fraction is None or self.kelly_fraction <= 0:
                raise ValueError(
                    "kelly_fraction must be provided and > 0 for kelly staking"
                )

        if self.min_odds is not None and self.min_odds <= 0:
            raise ValueError("min_odds must be > 0")

        if self.walk_forward:
            if self.train_window_matches is None or self.train_window_matches <= 0:
                raise ValueError(
                    "train_window_matches must be provided and > 0 when walk_forward=True"
                )
            if self.test_window_matches is None or self.test_window_matches <= 0:
                raise ValueError(
                    "test_window_matches must be provided and > 0 when walk_forward=True"
                )
            if self.step_matches is None or self.step_matches <= 0:
                raise ValueError(
                    "step_matches must be provided and > 0 when walk_forward=True"
                )

        if self.period_mode == "custom_day_groups" and not self.custom_periods:
            raise ValueError(
                "custom_periods is required when period_mode='custom_day_groups'"
            )

        if self.max_candidates_per_period is not None:
            if self.max_candidates_per_period <= 0:
                raise ValueError("max_candidates_per_period must be positive")
            if not self.rank_by:
                raise ValueError(
                    "rank_by is required when max_candidates_per_period is set"
                )

        return self
