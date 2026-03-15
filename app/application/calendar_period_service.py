from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.application.strategy_factory import build_strategy
from app.domain.simulation.config import SimulationConfig
from app.domain.simulation.context import RollingContext

DAY_TO_INDEX = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


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
    def run(self, matches, config: SimulationConfig):
        self._validate_request(config)

        if not matches:
            return {
                "calendar_periods": True,
                "period_mode": config.period_mode,
                "periods": [],
                "bets": [],
                "equity_curve": [],
                "starting_bankroll": config.starting_bankroll,
                "final_bankroll": config.starting_bankroll,
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

        periods = self._build_periods(matches, config.custom_periods)

        all_bets: list[dict[str, Any]] = []
        all_equity_points: list[dict[str, Any]] = []
        period_summaries: list[dict[str, Any]] = []

        running_bankroll = float(config.starting_bankroll)

        for bucket in periods:
            period_starting_bankroll = (
                float(config.starting_bankroll)
                if config.reset_bankroll_each_period
                else running_bankroll
            )

            candidates = self._build_candidates_for_period(bucket.matches, config)
            selected = self._rank_and_select_candidates(candidates, config)

            period_bets = self._build_period_bets(
                selected_candidates=selected,
                config=config,
                period_index=bucket.period_index,
                period_label=bucket.period_label,
            )

            period_settled_bets: list[dict[str, Any]] = []
            period_bankroll = period_starting_bankroll
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
                    config=config,
                )

                if stake <= 0:
                    continue

                settled = self._settle_bet(
                    bet=bet,
                    stake=stake,
                )

                period_bankroll += settled["profit"]

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

            if not config.reset_bankroll_each_period:
                running_bankroll = period_bankroll

        if config.reset_bankroll_each_period:
            total_profit = sum(b["profit"] for b in all_bets)
            final_bankroll = float(config.starting_bankroll) + total_profit
        else:
            final_bankroll = running_bankroll

        overall_metrics = self._compute_metrics(
            starting_bankroll=float(config.starting_bankroll),
            final_bankroll=final_bankroll,
            bets=all_bets,
            equity_curve=all_equity_points,
        )

        return {
            "calendar_periods": True,
            "period_mode": config.period_mode,
            "periods": period_summaries,
            "bets": all_bets,
            "equity_curve": all_equity_points,
            "starting_bankroll": round(float(config.starting_bankroll), 2),
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

    def _validate_request(self, config: SimulationConfig):
        if config.period_mode != "custom":
            raise ValueError("Unsupported period_mode for CalendarPeriodService")

        if not config.custom_periods:
            raise ValueError("custom_periods is required when period_mode='custom'")

    def _weekday_in_range(self, weekday: int, start_day: int, end_day: int) -> bool:
        if start_day <= end_day:
            return start_day <= weekday <= end_day
        return weekday >= start_day or weekday <= end_day

    def _resolve_period_start_date(
        self, kickoff: datetime, start_day: int, end_day: int
    ):
        weekday = kickoff.weekday()
        if not self._weekday_in_range(weekday, start_day, end_day):
            return None

        days_since_start = (weekday - start_day) % 7
        return kickoff.date() - timedelta(days=days_since_start)

    def _match_custom_period(self, kickoff: datetime, custom_periods):
        weekday = kickoff.weekday()
        matches = []

        for definition in custom_periods:
            start_idx = DAY_TO_INDEX[definition.start_day]
            end_idx = DAY_TO_INDEX[definition.end_day]
            if self._weekday_in_range(weekday, start_idx, end_idx):
                matches.append(definition)

        if not matches:
            return None

        if len(matches) > 1:
            labels = ", ".join(period.name for period in matches)
            raise ValueError(f"overlapping custom periods are not allowed: {labels}")

        return matches[0]

    def _build_periods(self, matches, custom_periods):
        sorted_matches = sorted(matches, key=lambda m: m.kickoff)
        buckets_by_key = OrderedDict()

        for match in sorted_matches:
            definition = self._match_custom_period(match.kickoff, custom_periods)
            if definition is None:
                continue

            start_idx = DAY_TO_INDEX[definition.start_day]
            end_idx = DAY_TO_INDEX[definition.end_day]
            period_start_date = self._resolve_period_start_date(
                match.kickoff, start_idx, end_idx
            )
            if period_start_date is None:
                continue

            bucket_key = f"{definition.name}|{period_start_date.isoformat()}"
            if bucket_key not in buckets_by_key:
                buckets_by_key[bucket_key] = {
                    "period_label": definition.name,
                    "matches": [],
                }

            buckets_by_key[bucket_key]["matches"].append(match)

        buckets = []
        for idx, (_, bucket) in enumerate(buckets_by_key.items()):
            bucket_matches = bucket["matches"]
            buckets.append(
                PeriodBucket(
                    period_index=idx,
                    period_label=bucket["period_label"],
                    start_kickoff=bucket_matches[0].kickoff,
                    end_kickoff=bucket_matches[-1].kickoff,
                    matches=bucket_matches,
                )
            )

        return buckets

    def _build_candidates_for_period(
        self, period_matches, config: SimulationConfig
    ) -> list[PeriodCandidate]:
        strategy = build_strategy(config)
        context = RollingContext(window_size=5)
        candidates: list[PeriodCandidate] = []

        for match in sorted(period_matches, key=lambda m: m.kickoff):
            decision = strategy.evaluate(match, context=context)

            if decision.place_bet and decision.selection:
                rank_value = self._compute_rank_value(
                    match, decision.selection, config.rank_by
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
        self, candidates: list[PeriodCandidate], config: SimulationConfig
    ) -> list[PeriodCandidate]:
        selected = list(candidates)

        if config.rank_by:
            selected = [c for c in selected if c.rank_value is not None]
            reverse = config.rank_order == "desc"
            selected.sort(key=lambda c: c.rank_value, reverse=reverse)

        if config.max_candidates_per_period is not None:
            if (
                config.require_full_candidate_count
                and len(selected) < config.max_candidates_per_period
            ):
                return []

            selected = selected[: config.max_candidates_per_period]

        return selected

    def _build_period_bets(
        self,
        *,
        selected_candidates: list[PeriodCandidate],
        config: SimulationConfig,
        period_index: int,
        period_label: str,
    ) -> list[dict[str, Any]]:
        if not selected_candidates:
            return []

        bets: list[dict[str, Any]] = []
        legs_per_bet = int(config.multiple_legs)

        if legs_per_bet == 1:
            for candidate in selected_candidates:
                bets.append(
                    self._make_bet_payload(
                        candidates=[candidate],
                        config=config,
                        period_index=period_index,
                        period_label=period_label,
                    )
                )
            return bets

        for i in range(0, len(selected_candidates), legs_per_bet):
            chunk = selected_candidates[i : i + legs_per_bet]
            if len(chunk) < legs_per_bet:
                continue

            bets.append(
                self._make_bet_payload(
                    candidates=chunk,
                    config=config,
                    period_index=period_index,
                    period_label=period_label,
                )
            )

        return bets

    def _make_bet_payload(
        self,
        *,
        candidates: list[PeriodCandidate],
        config: SimulationConfig,
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

            legs.append(
                {
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
            )

        return {
            "candidates": candidates,
            "legs": legs,
            "combined_odds": combined_odds,
            "combined_prob": combined_prob,
            "settled_at": settled_at,
            "meta": {
                "staking_method": config.staking_method,
                "multiple_legs": config.multiple_legs,
                "min_odds": config.min_odds,
                "period_index": period_index,
                "period_label": period_label,
            },
        }

    def _calculate_stake(
        self, *, bankroll: float, bet: dict[str, Any], config: SimulationConfig
    ) -> float:
        if bankroll <= 0:
            return 0.0

        if config.staking_method == "fixed":
            return round(float(config.fixed_stake or 0), 2)

        if config.staking_method == "percent":
            percent = float(config.percent_stake or 0)
            return round(bankroll * percent, 2)

        if config.staking_method == "kelly":
            fraction = float(config.kelly_fraction or 0)
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

    def _settle_bet(self, *, bet: dict[str, Any], stake: float) -> dict[str, Any]:
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

    def _max_drawdown_percent(self, equity_curve) -> float:
        if not equity_curve:
            return 0.0

        peak = None
        max_dd = 0.0
        for point in equity_curve:
            bankroll = float(point["bankroll"])
            if peak is None or bankroll > peak:
                peak = bankroll
            if peak and peak > 0:
                dd = (peak - bankroll) / peak
                max_dd = max(max_dd, dd)

        return round(max_dd * 100, 2)

    def _compute_rank_value(self, match, selection: str, rank_by: str | None):
        if not rank_by:
            return None

        features = getattr(match, "features", {}) or {}
        value = features.get(rank_by)
        if value is None:
            return None

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                return None
            return float(value)

        try:
            converted = float(value)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(converted):
            return None

        return converted

    def _odds_and_model_prob(self, match, selection: str):
        if selection == "H":
            return match.home_win_odds, match.model_home_prob
        if selection == "D":
            return match.draw_odds, match.model_draw_prob
        return match.away_win_odds, match.model_away_prob
