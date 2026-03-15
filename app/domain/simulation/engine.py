from itertools import combinations, groupby
from operator import attrgetter

from app.domain.simulation.config import SimulationConfig
from app.domain.simulation.context import RollingContext
from app.domain.simulation.entities import Match
from app.domain.simulation.models import SimulationRequest


class SettledBet:
    def __init__(
        self,
        matches,
        stake,
        combined_odds,
        selections,
        is_win,
        return_amount,
        profit,
        settled_at,
    ):
        self.matches = matches
        self.stake = stake
        self.combined_odds = combined_odds
        self.selections = selections
        self.is_win = is_win
        self.return_amount = return_amount
        self.profit = profit
        self.settled_at = settled_at


class Bet:
    def __init__(self, matches, stake, combined_odds, settles_at, selections):
        self.matches = matches  # list[Match]
        self.stake = stake
        self.combined_odds = combined_odds
        self.settles_at = settles_at
        self.selections = selections  # {match_id: "H"/"D"/"A"}


def settle_matured_bets(active_bets, kickoff, bankroll, team_locks, settle_all=False):
    settled = []

    for bet in active_bets[:]:
        if settle_all or bet.settles_at <= kickoff:
            is_win = all(
                match.result == bet.selections[match.id] for match in bet.matches
            )

            if is_win:
                return_amount = bet.stake * bet.combined_odds
            else:
                return_amount = 0

            profit = return_amount - bet.stake
            bankroll += return_amount

            settled.append(
                SettledBet(
                    matches=bet.matches,
                    stake=bet.stake,
                    combined_odds=bet.combined_odds,
                    selections=bet.selections,
                    is_win=is_win,
                    return_amount=return_amount,
                    profit=profit,
                    settled_at=bet.settles_at,
                )
            )

            active_bets.remove(bet)

            for match in bet.matches:
                team_locks.pop(match.home_team, None)
                team_locks.pop(match.away_team, None)

    return bankroll, settled


def calculate_stake(config: SimulationConfig, bankroll, combined_odds, combined_prob):
    if config.staking_method == "fixed":
        return config.fixed_stake

    if config.staking_method == "percent":
        return bankroll * config.percent_stake

    if config.staking_method == "kelly":
        if combined_prob is None:
            return None

        b = combined_odds - 1
        if b <= 0:
            return None

        f = (b * combined_prob - (1 - combined_prob)) / b

        if f <= 0:
            return None

        return bankroll * f * config.kelly_fraction

    return None


def build_valid_combo(
    eligible: list[tuple[Match, str]],
    multiple_legs: int,
) -> list[tuple[Match, str]] | None:
    for candidate in combinations(eligible, multiple_legs):
        teams = set()
        valid = True

        for match, _ in candidate:
            if match.home_team in teams or match.away_team in teams:
                valid = False
                break

            teams.add(match.home_team)
            teams.add(match.away_team)

        if valid:
            return list(candidate)

    return None


def calculate_metrics(settled_bets, starting_bankroll, final_bankroll):
    total_bets = len(settled_bets)
    total_wins = sum(1 for b in settled_bets if b.is_win)
    total_losses = total_bets - total_wins

    total_staked = sum(b.stake for b in settled_bets)
    total_profit = final_bankroll - starting_bankroll

    roi_percent = (total_profit / total_staked * 100) if total_staked > 0 else 0
    strike_rate_percent = (total_wins / total_bets * 100) if total_bets > 0 else 0

    gross_profit = sum(b.profit for b in settled_bets if b.profit > 0)
    gross_loss = abs(sum(b.profit for b in settled_bets if b.profit < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

    return {
        "total_bets": total_bets,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "roi_percent": round(roi_percent, 2),
        "strike_rate_percent": round(strike_rate_percent, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
    }


class SimulationEngine:
    def __init__(self, config: SimulationConfig | SimulationRequest, strategy):
        if isinstance(config, SimulationRequest):
            config = SimulationConfig.from_request(config)

        self.config = config
        self.strategy = strategy

        # Simulation state
        self.context = RollingContext(window_size=5)
        self.bankroll = config.starting_bankroll
        self.active_bets = []
        self.settled_bets = []
        self.team_locks = {}
        self.pending_candidates = []

        # Metrics tracking
        self.max_drawdown = 0
        self.peak_bankroll = self.bankroll
        self.equity_curve = [{"t": None, "bankroll": round(self.bankroll, 2)}]

    def run(self, matches: list[Match]):
        available_features = sorted(
            {k for m in matches for k in (getattr(m, "features", {}) or {}).keys()}
        )

        for kickoff, group in groupby(matches, key=attrgetter("kickoff")):
            batch = list(group)
            self._settle_matured(kickoff)
            self._process_kickoff_batch(batch)

        self._final_settlement(matches)

        metrics = calculate_metrics(
            self.settled_bets,
            self.config.starting_bankroll,
            self.bankroll,
        )

        return {
            "bets": [self._serialize_bet(b) for b in self.settled_bets],
            "final_bankroll": round(self.bankroll, 2),
            "available_features": available_features,
            "max_drawdown_percent": round(self.max_drawdown * 100, 2),
            "equity_curve": self.equity_curve,
            "run_config": self.config.to_run_config(),
            **metrics,
        }

    def _settle_matured(self, kickoff):
        self.bankroll, newly_settled = settle_matured_bets(
            self.active_bets,
            kickoff,
            self.bankroll,
            self.team_locks,
        )

        self.settled_bets.extend(newly_settled)
        for b in newly_settled:
            self.equity_curve.append(
                {"t": b.settled_at.isoformat(), "bankroll": round(self.bankroll, 2)}
            )
        self._update_drawdown()

    def _process_kickoff_batch(self, batch):
        eligible = []

        for match in batch:
            if match.home_team in self.team_locks or match.away_team in self.team_locks:
                continue

            decision = self.strategy.evaluate(match, context=self.context)
            if not decision.place_bet:
                continue

            eligible.append((match, decision.selection))

        if self.config.multiple_legs <= 1:
            for candidate in eligible:
                self._attempt_place_bet([candidate])
        else:
            self.pending_candidates.extend(eligible)

            while len(self.pending_candidates) >= self.config.multiple_legs:
                combo = build_valid_combo(
                    self.pending_candidates,
                    self.config.multiple_legs,
                )

                if not combo:
                    break

                placed = self._attempt_place_bet(combo)
                if not placed:
                    break

                used_match_ids = {match.id for match, _ in combo}
                self.pending_candidates = [
                    candidate
                    for candidate in self.pending_candidates
                    if candidate[0].id not in used_match_ids
                ]

        for match in batch:
            self.context.update(match)

    def _attempt_place_bet(self, combo: list[tuple[Match, str]]):
        combined_odds = 1
        combined_prob = 1
        selections = {}

        for match, selection in combo:
            odds = {
                "H": match.home_win_odds,
                "D": match.draw_odds,
                "A": match.away_win_odds,
            }[selection]

            if self.config.min_odds is not None and odds < self.config.min_odds:
                return False

            combined_odds *= odds
            selections[match.id] = selection

            if self.config.staking_method == "kelly":
                prob = {
                    "H": match.model_home_prob,
                    "D": match.model_draw_prob,
                    "A": match.model_away_prob,
                }[selection]

                if prob is None:
                    return False

                combined_prob *= prob
            else:
                combined_prob = None

        stake = calculate_stake(
            self.config,
            self.bankroll,
            combined_odds,
            combined_prob,
        )
        if stake is None or stake <= 0 or stake > self.bankroll:
            return False

        settles_at = max(match.kickoff for match, _ in combo)
        matches = [match for match, _ in combo]

        self.bankroll -= stake
        self.active_bets.append(
            Bet(
                matches=matches,
                stake=stake,
                combined_odds=combined_odds,
                settles_at=settles_at,
                selections=selections,
            )
        )

        for match in matches:
            self.team_locks[match.home_team] = True
            self.team_locks[match.away_team] = True

        return True

    def _final_settlement(self, matches):
        if matches:
            final_kickoff = max(match.kickoff for match in matches)
            self.bankroll, newly_settled = settle_matured_bets(
                self.active_bets,
                final_kickoff,
                self.bankroll,
                self.team_locks,
                settle_all=True,
            )
            self.settled_bets.extend(newly_settled)

            for b in newly_settled:
                self.equity_curve.append(
                    {"t": b.settled_at.isoformat(), "bankroll": round(self.bankroll, 2)}
                )
            self._update_drawdown()

    def _update_drawdown(self):
        if self.bankroll > self.peak_bankroll:
            self.peak_bankroll = self.bankroll

        if self.peak_bankroll > 0:
            drawdown = (self.peak_bankroll - self.bankroll) / self.peak_bankroll
            self.max_drawdown = max(self.max_drawdown, drawdown)

    def _serialize_bet(self, bet: SettledBet):
        return {
            "stake": round(bet.stake, 2),
            "combined_odds": round(bet.combined_odds, 4),
            "is_win": bet.is_win,
            "return_amount": round(bet.return_amount, 2),
            "profit": round(bet.profit, 2),
            "settled_at": bet.settled_at.isoformat(),
            "legs": [
                {
                    "match_id": str(match.id),
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "selection": bet.selections[match.id],
                    "result": match.result,
                    "odds": {
                        "H": match.home_win_odds,
                        "D": match.draw_odds,
                        "A": match.away_win_odds,
                    }[bet.selections[match.id]],
                }
                for match in bet.matches
            ],
        }
