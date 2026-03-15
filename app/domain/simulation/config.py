from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from app.domain.simulation.models import CustomPeriodDefinition, SimulationRequest


@dataclass(frozen=True)
class StrategyConfig:
    selection: Literal["H", "D", "A"]
    rule_expression: str | None


@dataclass(frozen=True)
class StakingConfig:
    method: Literal["fixed", "percent", "kelly"]
    fixed_stake: float | None
    percent_stake: float | None
    kelly_fraction: float | None


@dataclass(frozen=True)
class WalkForwardConfig:
    enabled: bool
    train_window_matches: int | None
    test_window_matches: int | None
    step_matches: int | None


@dataclass(frozen=True)
class CalendarConfig:
    period_mode: Literal["none", "custom"]
    custom_periods: list[CustomPeriodDefinition]
    reset_bankroll_each_period: bool


@dataclass(frozen=True)
class RankingConfig:
    max_candidates_per_period: int | None
    rank_by: str | None
    rank_order: Literal["asc", "desc"]
    require_full_candidate_count: bool


@dataclass(frozen=True)
class SimulationConfig:
    league: str | None
    leagues: list[str] | None
    season: str
    strategy: StrategyConfig
    staking: StakingConfig
    starting_bankroll: float
    multiple_legs: int
    min_odds: float | None
    walk_forward: WalkForwardConfig
    calendar: CalendarConfig
    ranking: RankingConfig

    @classmethod
    def from_request(cls, request: SimulationRequest) -> "SimulationConfig":
        return cls(
            league=request.league,
            leagues=list(request.leagues) if request.leagues else None,
            season=request.season,
            strategy=StrategyConfig(
                selection=request.selection,
                rule_expression=request.rule_expression,
            ),
            staking=StakingConfig(
                method=request.staking_method,
                fixed_stake=request.fixed_stake,
                percent_stake=request.percent_stake,
                kelly_fraction=request.kelly_fraction,
            ),
            starting_bankroll=float(request.starting_bankroll),
            multiple_legs=int(request.multiple_legs),
            min_odds=request.min_odds,
            walk_forward=WalkForwardConfig(
                enabled=bool(request.walk_forward),
                train_window_matches=request.train_window_matches,
                test_window_matches=request.test_window_matches,
                step_matches=request.step_matches,
            ),
            calendar=CalendarConfig(
                period_mode=request.period_mode,
                custom_periods=list(request.custom_periods or []),
                reset_bankroll_each_period=bool(request.reset_bankroll_each_period),
            ),
            ranking=RankingConfig(
                max_candidates_per_period=request.max_candidates_per_period,
                rank_by=request.rank_by,
                rank_order=request.rank_order,
                require_full_candidate_count=bool(request.require_full_candidate_count),
            ),
        )

    @property
    def selection(self) -> Literal["H", "D", "A"]:
        return self.strategy.selection

    @property
    def rule_expression(self) -> str | None:
        return self.strategy.rule_expression

    @property
    def staking_method(self) -> Literal["fixed", "percent", "kelly"]:
        return self.staking.method

    @property
    def fixed_stake(self) -> float | None:
        return self.staking.fixed_stake

    @property
    def percent_stake(self) -> float | None:
        return self.staking.percent_stake

    @property
    def kelly_fraction(self) -> float | None:
        return self.staking.kelly_fraction

    @property
    def walk_forward_enabled(self) -> bool:
        return self.walk_forward.enabled

    @property
    def train_window_matches(self) -> int | None:
        return self.walk_forward.train_window_matches

    @property
    def test_window_matches(self) -> int | None:
        return self.walk_forward.test_window_matches

    @property
    def step_matches(self) -> int | None:
        return self.walk_forward.step_matches

    @property
    def period_mode(self) -> Literal["none", "custom"]:
        return self.calendar.period_mode

    @property
    def custom_periods(self) -> list[CustomPeriodDefinition]:
        return self.calendar.custom_periods

    @property
    def reset_bankroll_each_period(self) -> bool:
        return self.calendar.reset_bankroll_each_period

    @property
    def max_candidates_per_period(self) -> int | None:
        return self.ranking.max_candidates_per_period

    @property
    def rank_by(self) -> str | None:
        return self.ranking.rank_by

    @property
    def rank_order(self) -> Literal["asc", "desc"]:
        return self.ranking.rank_order

    @property
    def require_full_candidate_count(self) -> bool:
        return self.ranking.require_full_candidate_count

    def with_updates(self, **changes) -> "SimulationConfig":
        return replace(self, **changes)

    def with_starting_bankroll(self, bankroll: float) -> "SimulationConfig":
        return replace(self, starting_bankroll=float(bankroll))

    def without_walk_forward(self) -> "SimulationConfig":
        return replace(
            self,
            walk_forward=replace(self.walk_forward, enabled=False),
        )

    def to_run_config(self) -> dict:
        return {
            "league": self.league,
            "season": self.season,
            "selection": self.selection,
            "staking_method": self.staking_method,
            "fixed_stake": self.fixed_stake,
            "percent_stake": self.percent_stake,
            "kelly_fraction": self.kelly_fraction,
            "multiple_legs": self.multiple_legs,
            "min_odds": self.min_odds,
        }
