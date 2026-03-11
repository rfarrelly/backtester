from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.application.strategy_factory import build_strategy
from app.domain.simulation.context import RollingContext
from app.domain.simulation.engine import SimulationEngine


@dataclass
class PeriodBucket:
    period_index: int
    period_label: str
    start_kickoff: datetime
    end_kickoff: datetime
    matches: list


@dataclass
class PeriodCandidate:
    match: object
    selection: str
    rank_value: float | None


class CalendarPeriodService:
    def run(self, matches, request):
        self._validate_request(request)

        if not matches:
            return {
                "calendar_periods": True,
                "period_mode": request.period_mode,
                "periods": [],
                "bets": [],
                "equity_curve": [],
                "starting_bankroll": request.starting_bankroll,
                "final_bankroll": request.starting_bankroll,
                "roi_percent": 0.0,
                "total_periods": 0,
                "total_bets": 0,
            }

        periods = self._build_periods(matches, request.custom_periods or {})

        combined_periods = []
        combined_bets = []
        combined_equity_curve = []

        running_bankroll = request.starting_bankroll

        for bucket in periods:
            period_starting_bankroll = (
                request.starting_bankroll
                if request.reset_bankroll_each_period
                else running_bankroll
            )

            selected_matches = self._select_matches_for_period(bucket.matches, request)

            segment_request = request.model_copy(
                update={
                    "starting_bankroll": period_starting_bankroll,
                    "walk_forward": False,
                    "period_mode": "none",
                    "custom_periods": None,
                    "reset_bankroll_each_period": False,
                    "max_candidates_per_period": None,
                    "rank_by": None,
                    "rank_order": "asc",
                    "require_full_candidate_count": False,
                }
            )

            strategy = build_strategy(segment_request)
            engine = SimulationEngine(segment_request, strategy)
            result = engine.run(selected_matches)

            period_summary = {
                "period_index": bucket.period_index,
                "period_label": bucket.period_label,
                "start_kickoff": bucket.start_kickoff.isoformat(),
                "end_kickoff": bucket.end_kickoff.isoformat(),
                "starting_bankroll": period_starting_bankroll,
                "final_bankroll": result["final_bankroll"],
                "roi_percent": result["roi_percent"],
                "total_bets": result["total_bets"],
                "total_wins": result.get("total_wins", 0),
                "total_losses": result.get("total_losses", 0),
                "strike_rate_percent": result.get("strike_rate_percent", 0),
                "max_drawdown_percent": result.get("max_drawdown_percent", 0),
                "profit_factor": result.get("profit_factor"),
            }
            combined_periods.append(period_summary)
            combined_bets.extend(result["bets"])

            for point in result.get("equity_curve", []):
                combined_equity_curve.append(
                    {
                        **point,
                        "period_index": bucket.period_index,
                        "period_label": bucket.period_label,
                    }
                )

            if not request.reset_bankroll_each_period:
                running_bankroll = result["final_bankroll"]

        final_bankroll = (
            request.starting_bankroll
            if request.reset_bankroll_each_period and combined_periods
            else running_bankroll
        )

        if request.reset_bankroll_each_period and combined_periods:
            # In reset mode, aggregate final bankroll is less meaningful.
            # Keep it as the sum of period profits over original starting bankroll.
            total_profit = sum(
                p["final_bankroll"] - p["starting_bankroll"] for p in combined_periods
            )
            final_bankroll = round(request.starting_bankroll + total_profit, 2)

        roi_percent = (
            ((final_bankroll - request.starting_bankroll) / request.starting_bankroll)
            * 100
            if request.starting_bankroll
            else 0
        )

        return {
            "calendar_periods": True,
            "period_mode": request.period_mode,
            "periods": combined_periods,
            "bets": combined_bets,
            "equity_curve": combined_equity_curve,
            "starting_bankroll": request.starting_bankroll,
            "final_bankroll": round(final_bankroll, 2),
            "roi_percent": round(roi_percent, 2),
            "total_periods": len(combined_periods),
            "total_bets": sum(p["total_bets"] for p in combined_periods),
        }

    def _validate_request(self, request):
        if request.period_mode != "custom_day_groups":
            raise ValueError("Unsupported period_mode for CalendarPeriodService")

        if not request.custom_periods:
            raise ValueError(
                "custom_periods is required when period_mode='custom_day_groups'"
            )

        seen_days = set()
        for label, days in request.custom_periods.items():
            if not days:
                raise ValueError(f"custom_periods['{label}'] cannot be empty")

            for day in days:
                if day < 0 or day > 6:
                    raise ValueError("Weekday values must be between 0 and 6")
                if day in seen_days:
                    raise ValueError(
                        "A weekday cannot belong to more than one custom period"
                    )
                seen_days.add(day)

        if request.max_candidates_per_period is not None:
            if request.max_candidates_per_period <= 0:
                raise ValueError("max_candidates_per_period must be positive")
            if not request.rank_by:
                raise ValueError(
                    "rank_by is required when max_candidates_per_period is set"
                )

    def _build_periods(
        self, matches, custom_periods: dict[str, list[int]]
    ) -> list[PeriodBucket]:
        weekday_to_label = {}
        for label, weekdays in custom_periods.items():
            for weekday in weekdays:
                weekday_to_label[weekday] = label

        sorted_matches = sorted(matches, key=lambda m: m.kickoff)

        buckets: list[PeriodBucket] = []
        current_label = None
        current_matches = []
        period_index = 0

        for match in sorted_matches:
            weekday = match.kickoff.weekday()
            label = weekday_to_label.get(weekday)

            # Skip matches not covered by any period definition
            if label is None:
                if current_matches:
                    buckets.append(
                        PeriodBucket(
                            period_index=period_index,
                            period_label=current_label,
                            start_kickoff=current_matches[0].kickoff,
                            end_kickoff=current_matches[-1].kickoff,
                            matches=current_matches,
                        )
                    )
                    period_index += 1
                    current_matches = []
                    current_label = None
                continue

            if current_label is None:
                current_label = label
                current_matches = [match]
                continue

            if label == current_label:
                current_matches.append(match)
            else:
                buckets.append(
                    PeriodBucket(
                        period_index=period_index,
                        period_label=current_label,
                        start_kickoff=current_matches[0].kickoff,
                        end_kickoff=current_matches[-1].kickoff,
                        matches=current_matches,
                    )
                )
                period_index += 1
                current_label = label
                current_matches = [match]

        if current_matches:
            buckets.append(
                PeriodBucket(
                    period_index=period_index,
                    period_label=current_label,
                    start_kickoff=current_matches[0].kickoff,
                    end_kickoff=current_matches[-1].kickoff,
                    matches=current_matches,
                )
            )

        return buckets

    def _select_matches_for_period(self, period_matches, request):
        # First evaluate all matches in the period using the strategy and a rolling context
        strategy = build_strategy(request)
        context = RollingContext(window_size=5)

        candidates: list[PeriodCandidate] = []

        for match in sorted(period_matches, key=lambda m: m.kickoff):
            decision = strategy.evaluate(match, context=context)

            if decision.place_bet and decision.selection:
                rank_value = self._compute_rank_value(
                    match, decision.selection, request.rank_by
                )
                candidates.append(
                    PeriodCandidate(
                        match=match,
                        selection=decision.selection,
                        rank_value=rank_value,
                    )
                )

            # Keep context progression realistic within the period
            context.update(match)

        # Ranking is optional
        if request.rank_by:
            candidates = [c for c in candidates if c.rank_value is not None]
            reverse = request.rank_order == "desc"
            candidates.sort(key=lambda c: c.rank_value, reverse=reverse)

        if request.max_candidates_per_period is not None:
            if (
                request.require_full_candidate_count
                and len(candidates) < request.max_candidates_per_period
            ):
                return []

            candidates = candidates[: request.max_candidates_per_period]

        # Convert selected candidates back into match objects for the engine run.
        # The engine will re-evaluate them, but only within this selected subset.
        selected_matches = [c.match for c in candidates]
        selected_match_ids = {m.id for m in selected_matches}

        return [m for m in period_matches if m.id in selected_match_ids]

    def _compute_rank_value(self, match, selection: str, rank_by: str | None):
        if not rank_by:
            return None

        # Built-in fields
        if hasattr(match, rank_by):
            value = getattr(match, rank_by)
            return self._to_float_or_none(value)

        # Uploaded feature dict
        features = getattr(match, "features", None)
        if isinstance(features, dict) and rank_by in features:
            return self._to_float_or_none(features[rank_by])

        # Derived "edge"
        if rank_by == "edge":
            odds_map = {
                "H": match.home_win_odds,
                "D": match.draw_odds,
                "A": match.away_win_odds,
            }
            prob_map = {
                "H": match.model_home_prob,
                "D": match.model_draw_prob,
                "A": match.model_away_prob,
            }
            odds = odds_map.get(selection)
            model_prob = prob_map.get(selection)
            if odds and model_prob is not None:
                implied_prob = 1 / odds
                return model_prob - implied_prob
            return None

        return None

    def _to_float_or_none(self, value):
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
