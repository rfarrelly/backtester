from typing import Literal

from pydantic import BaseModel, model_validator

DAY_TO_INDEX = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _covered_days(start_day: str, end_day: str) -> set[int]:
    start = DAY_TO_INDEX[start_day]
    end = DAY_TO_INDEX[end_day]

    if start <= end:
        return set(range(start, end + 1))

    return set(range(start, 7)) | set(range(0, end + 1))


class CustomPeriodDefinition(BaseModel):
    name: str
    start_day: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    end_day: Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    @model_validator(mode="after")
    def validate_period(self):
        if not self.name or not self.name.strip():
            raise ValueError("custom period name is required")
        return self


class SimulationRequest(BaseModel):
    # Dataset filtering
    league: str | None = None
    leagues: list[str] | None = None
    season: str

    # Strategy
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
    period_mode: Literal["none", "custom"] = "none"
    custom_periods: list[CustomPeriodDefinition] | None = None
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

        if self.period_mode == "custom":
            if not self.custom_periods:
                raise ValueError("custom_periods is required when period_mode='custom'")

            names = [period.name.strip().lower() for period in self.custom_periods]
            if len(names) != len(set(names)):
                raise ValueError("custom period names must be unique")

            covered_by_period: list[tuple[str, set[int]]] = []
            for period in self.custom_periods:
                covered_by_period.append(
                    (period.name, _covered_days(period.start_day, period.end_day))
                )

            for i in range(len(covered_by_period)):
                name_a, days_a = covered_by_period[i]
                for j in range(i + 1, len(covered_by_period)):
                    name_b, days_b = covered_by_period[j]
                    if days_a & days_b:
                        raise ValueError(
                            f"overlapping custom periods are not allowed: {name_a} and {name_b}"
                        )

        if self.max_candidates_per_period is not None:
            if self.max_candidates_per_period <= 0:
                raise ValueError("max_candidates_per_period must be positive")
            if not self.rank_by:
                raise ValueError(
                    "rank_by is required when max_candidates_per_period is set"
                )

        return self
