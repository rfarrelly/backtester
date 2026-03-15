from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.application.strategy_factory import build_strategy
from app.domain.simulation.context import RollingContext


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
                "total_wins": 0,
                "total_losses": 0,
                "strike_rate_percent": 0.0,
                "max_drawdown_percent": 0.0,
                "profit_factor": None,
                "average_odds": None,
                "total_profit": 0.0,
            }

        periods = self._build_periods(matches, request.custom_periods or {})

        all_bets: list[dict[str, Any]] = []
        all_equity_points: list[dict[str, Any]] = []
        period_summaries: list[dict[str, Any]] = []

        running_bankroll = float(request.starting_bankroll)
        peak_bankroll = running_bankroll

        for bucket in periods:
            period_starting_bankroll = (
                float(request.starting_bankroll)
                if request.reset_bankroll_each_period
                else running_bankroll
            )

            candidates = self._build_candidates_for_period(bucket.matches, request)
            selected = self._rank_and_select_candidates(candidates, request)

            # Debug output kept intentionally because it is useful here
            print("SELECTION PERIOD CANDIDATES")
            for c in selected:
                print(
                    bucket.period_label,
                    c.match.kickoff,
                    c.match.league,
                    c.selection,
                    c.match.home_team,
                    c.match.away_team,
                )

            period_bets = self._build_period_bets(
                selected_candidates=selected,
                request=request,
                period_index=bucket.period_index,
                period_label=bucket.period_label,
                starting_bankroll=period_starting_bankroll,
            )

            # Settle bets in order
            period_settled_bets: list[dict[str, Any]] = []
            period_bankroll = period_starting_bankroll
            period_peak = period_bankroll
            period_equity_curve = [
                {
                    "t": bucket.start_kickoff.isoformat(),
                    "bankroll": round(period_bankroll, 2),
                    "period_index": bucket.period_index,
                    "period_label": bucket.period_label,
                }
            ]

            for bet in period_bets:
                stake = self._calculate_stake(
                    bankroll=period_bankroll,
                    bet=bet,
                    request=request,
                )

                if stake <= 0:
                    continue

                settled = self._settle_bet(
                    bet=bet,
                    stake=stake,
                    request=request,
                )

                period_bankroll += settled["profit"]
                period_peak = max(period_peak, period_bankroll)

                settled["meta"] = {
                    **settled.get("meta", {}),
                    "period_index": bucket.period_index,
                    "period_label": bucket.period_label,
                }

                period_settled_bets.append(settled)
                period_equity_curve.append(
                    {
                        "t": settled["settled_at"],
                        "bankroll": round(period_bankroll, 2),
                        "period_index": bucket.period_index,
                        "period_label": bucket.period_label,
                    }
                )

            period_metrics = self._compute_metrics(
                starting_bankroll=period_starting_bankroll,
                final_bankroll=period_bankroll,
                bets=period_settled_bets,
                equity_curve=period_equity_curve,
            )

            period_summaries.append(
                {
                    "period_index": bucket.period_index,
                    "period_label": bucket.period_label,
                    "start_kickoff": bucket.start_kickoff.isoformat(),
                    "end_kickoff": bucket.end_kickoff.isoformat(),
                    "starting_bankroll": round(period_starting_bankroll, 2),
                    "final_bankroll": round(period_bankroll, 2),
                    "roi_percent": period_metrics["roi_percent"],
                    "total_bets": period_metrics["total_bets"],
                    "total_wins": period_metrics["total_wins"],
                    "total_losses": period_metrics["total_losses"],
                    "strike_rate_percent": period_metrics["strike_rate_percent"],
                    "max_drawdown_percent": period_metrics["max_drawdown_percent"],
                    "profit_factor": period_metrics["profit_factor"],
                    "matches_in_period": len(bucket.matches),
                    "eligible_candidates": len(candidates),
                    "selected_candidates": len(selected),
                    "bets_created": len(period_settled_bets),
                }
            )

            all_bets.extend(period_settled_bets)
            all_equity_points.extend(period_equity_curve)

            if not request.reset_bankroll_each_period:
                running_bankroll = period_bankroll
                peak_bankroll = max(peak_bankroll, running_bankroll)

        if request.reset_bankroll_each_period:
            total_profit = sum(b["profit"] for b in all_bets)
            final_bankroll = float(request.starting_bankroll) + total_profit
        else:
            final_bankroll = running_bankroll

        overall_metrics = self._compute_metrics(
            starting_bankroll=float(request.starting_bankroll),
            final_bankroll=final_bankroll,
            bets=all_bets,
            equity_curve=all_equity_points,
        )

        return {
            "calendar_periods": True,
            "period_mode": request.period_mode,
            "periods": period_summaries,
            "bets": all_bets,
            "equity_curve": all_equity_points,
            "starting_bankroll": round(float(request.starting_bankroll), 2),
            "final_bankroll": round(final_bankroll, 2),
            "roi_percent": overall_metrics["roi_percent"],
            "total_periods": len(period_summaries),
            "total_bets": overall_metrics["total_bets"],
            "total_wins": overall_metrics["total_wins"],
            "total_losses": overall_metrics["total_losses"],
            "strike_rate_percent": overall_metrics["strike_rate_percent"],
            "max_drawdown_percent": overall_metrics["max_drawdown_percent"],
            "profit_factor": overall_metrics["profit_factor"],
            "average_odds": overall_metrics["average_odds"],
            "total_profit": overall_metrics["total_profit"],
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

        if request.multiple_legs <= 0:
            raise ValueError("multiple_legs must be positive")

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

    def _build_candidates_for_period(
        self, period_matches, request
    ) -> list[PeriodCandidate]:
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

            context.update(match)

        return candidates

    def _rank_and_select_candidates(
        self, candidates: list[PeriodCandidate], request
    ) -> list[PeriodCandidate]:
        selected = list(candidates)

        if request.rank_by:
            selected = [c for c in selected if c.rank_value is not None]
            reverse = request.rank_order == "desc"
            selected.sort(key=lambda c: c.rank_value, reverse=reverse)

        if request.max_candidates_per_period is not None:
            if (
                request.require_full_candidate_count
                and len(selected) < request.max_candidates_per_period
            ):
                return []

            selected = selected[: request.max_candidates_per_period]

        return selected

    def _build_period_bets(
        self,
        *,
        selected_candidates: list[PeriodCandidate],
        request,
        period_index: int,
        period_label: str,
        starting_bankroll: float,
    ) -> list[dict[str, Any]]:
        if not selected_candidates:
            return []

        bets: list[dict[str, Any]] = []
        legs_per_bet = int(request.multiple_legs)

        if legs_per_bet == 1:
            for candidate in selected_candidates:
                bets.append(
                    self._make_bet_payload(
                        candidates=[candidate],
                        request=request,
                        period_index=period_index,
                        period_label=period_label,
                    )
                )
            return bets

        # For multiples, chunk the ranked pool deterministically
        for i in range(0, len(selected_candidates), legs_per_bet):
            chunk = selected_candidates[i : i + legs_per_bet]
            if len(chunk) < legs_per_bet:
                continue

            bets.append(
                self._make_bet_payload(
                    candidates=chunk,
                    request=request,
                    period_index=period_index,
                    period_label=period_label,
                )
            )

        return bets

    def _make_bet_payload(
        self,
        *,
        candidates: list[PeriodCandidate],
        request,
        period_index: int,
        period_label: str,
    ):
        combined_odds = 1.0
        combined_prob = 1.0
        settled_at = max(c.match.kickoff for c in candidates).isoformat()

        legs = []
        for candidate in candidates:
            match = candidate.match
            selection = candidate.selection

            odds, model_prob = self._odds_and_model_prob(match, selection)
            if odds:
                combined_odds *= odds

            if model_prob is not None:
                combined_prob *= model_prob
            else:
                combined_prob = None

            implied_prob = (1 / odds) if odds else None
            edge = (
                (model_prob - implied_prob)
                if (model_prob is not None and implied_prob is not None)
                else None
            )

            leg = {
                "match_id": str(match.id),
                "kickoff": match.kickoff.isoformat(),
                "home_team": match.home_team,
                "away_team": match.away_team,
                "result": match.result,
                "selection": selection,
                "odds": odds,
                "implied_prob": implied_prob,
                "model_prob": model_prob,
                "edge": edge,
                "features": getattr(match, "features", {}) or {},
                "league": getattr(match, "league", None),
            }
            legs.append(leg)

        return {
            "candidates": candidates,
            "legs": legs,
            "combined_odds": combined_odds,
            "combined_prob": combined_prob,
            "settled_at": settled_at,
            "meta": {
                "strategy_type": request.strategy_type,
                "staking_method": request.staking_method,
                "multiple_legs": request.multiple_legs,
                "min_odds": request.min_odds,
                "period_index": period_index,
                "period_label": period_label,
            },
        }

    def _calculate_stake(
        self, *, bankroll: float, bet: dict[str, Any], request
    ) -> float:
        if bankroll <= 0:
            return 0.0

        if request.staking_method == "fixed":
            return round(float(request.fixed_stake or 0), 2)

        if request.staking_method == "percent":
            percent = float(request.percent_stake or 0)
            return round(bankroll * percent, 2)

        if request.staking_method == "kelly":
            fraction = float(request.kelly_fraction or 0)
            combined_odds = bet["combined_odds"]
            combined_prob = bet["combined_prob"]

            if combined_prob is None or not combined_odds or combined_odds <= 1:
                return 0.0

            b = combined_odds - 1
            p = combined_prob
            q = 1 - p
            kelly = ((b * p) - q) / b if b > 0 else 0.0
            kelly = max(kelly, 0.0)

            return round(bankroll * kelly * fraction, 2)

        return 0.0

    def _settle_bet(
        self, *, bet: dict[str, Any], stake: float, request
    ) -> dict[str, Any]:
        is_win = all(leg["selection"] == leg["result"] for leg in bet["legs"])
        return_amount = stake * bet["combined_odds"] if is_win else 0.0
        profit = return_amount - stake

        return {
            "stake": round(stake, 2),
            "combined_odds": round(bet["combined_odds"], 4),
            "is_win": is_win,
            "profit": round(profit, 2),
            "return_amount": round(return_amount, 2),
            "settled_at": bet["settled_at"],
            "legs": bet["legs"],
            "meta": bet["meta"],
        }

    def _compute_metrics(
        self, *, starting_bankroll: float, final_bankroll: float, bets, equity_curve
    ):
        total_bets = len(bets)
        total_wins = sum(1 for b in bets if b["is_win"])
        total_losses = total_bets - total_wins
        total_profit = round(sum(b["profit"] for b in bets), 2)

        roi_percent = (
            round(((final_bankroll - starting_bankroll) / starting_bankroll) * 100, 2)
            if starting_bankroll
            else 0.0
        )

        strike_rate_percent = (
            round((total_wins / total_bets) * 100, 2) if total_bets else 0.0
        )

        gross_profit = sum(max(b["profit"], 0) for b in bets)
        gross_loss = abs(sum(min(b["profit"], 0) for b in bets))
        profit_factor = round(gross_profit / gross_loss, 4) if gross_loss > 0 else None

        avg_odds = (
            round(sum(b["combined_odds"] for b in bets) / total_bets, 4)
            if total_bets
            else None
        )

        max_drawdown_percent = self._max_drawdown_percent(equity_curve)

        return {
            "final_bankroll": round(final_bankroll, 2),
            "roi_percent": roi_percent,
            "total_bets": total_bets,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "strike_rate_percent": strike_rate_percent,
            "max_drawdown_percent": max_drawdown_percent,
            "profit_factor": profit_factor,
            "average_odds": avg_odds,
            "total_profit": total_profit,
        }

    def _max_drawdown_percent(self, equity_curve):
        if not equity_curve:
            return 0.0

        peak = None
        max_dd = 0.0

        for point in equity_curve:
            bankroll = float(point["bankroll"])
            if peak is None or bankroll > peak:
                peak = bankroll

            if peak and peak > 0:
                dd = ((peak - bankroll) / peak) * 100
                max_dd = max(max_dd, dd)

        return round(max_dd, 2)

    def _compute_rank_value(self, match, selection: str, rank_by: str | None):
        if not rank_by:
            return None

        if hasattr(match, rank_by):
            return self._to_float_or_none(getattr(match, rank_by))

        features = getattr(match, "features", None)
        if isinstance(features, dict) and rank_by in features:
            return self._to_float_or_none(features[rank_by])

        if rank_by == "edge":
            odds, model_prob = self._odds_and_model_prob(match, selection)
            if odds and model_prob is not None:
                return model_prob - (1 / odds)
            return None

        return None

    def _odds_and_model_prob(self, match, selection: str):
        odds_map = {
            "H": getattr(match, "home_win_odds", None),
            "D": getattr(match, "draw_odds", None),
            "A": getattr(match, "away_win_odds", None),
        }
        prob_map = {
            "H": getattr(match, "model_home_prob", None),
            "D": getattr(match, "model_draw_prob", None),
            "A": getattr(match, "model_away_prob", None),
        }
        return odds_map.get(selection), prob_map.get(selection)

    def _to_float_or_none(self, value):
        try:
            if value is None:
                return None
            value = float(value)
            if not math.isfinite(value):
                return None
            return value
        except (TypeError, ValueError):
            return None
