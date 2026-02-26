from itertools import combinations, groupby
from operator import attrgetter

from app.domain.simulation.context import RollingContext
from app.domain.simulation.entities import Match


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


def calculate_stake(request, bankroll, combined_odds, combined_prob):
    if request.staking_method == "fixed":
        return request.fixed_stake

    if request.staking_method == "percent":
        return bankroll * request.percent_stake

    if request.staking_method == "kelly":
        if combined_prob is None:
            return None

        b = combined_odds - 1
        if b <= 0:
            return None
        f = (b * combined_prob - (1 - combined_prob)) / b

        if f <= 0:
            return None

        return bankroll * f * request.kelly_fraction

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


class SimulationEngine:
    def __init__(self, request, strategy):
        self.request = request
        self.strategy = strategy

        # Simulation state
        self.context = RollingContext(window_size=5)
        self.bankroll = request.starting_bankroll
        self.active_bets = []
        self.settled_bets = []
        self.team_locks = {}

        # Metrics tracking
        self.max_drawdown = 0
        self.peak_bankroll = self.bankroll

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def run(self, matches: list[Match]):
        for kickoff, group in groupby(matches, key=attrgetter("kickoff")):
            batch = list(group)

            self._settle_matured(kickoff)
            self._process_kickoff_batch(batch)

        self._final_settlement(matches)

        metrics = calculate_metrics(
            self.settled_bets,
            self.request.starting_bankroll,
            self.bankroll,
        )

        return {
            "bets": self.settled_bets,
            "final_bankroll": round(self.bankroll, 2),
            "max_drawdown_percent": round(self.max_drawdown * 100, 2),
            **metrics,
        }

    # --------------------------------------------------
    # Core Steps
    # --------------------------------------------------

    def _settle_matured(self, kickoff):
        self.bankroll, newly_settled = settle_matured_bets(
            self.active_bets,
            kickoff,
            self.bankroll,
            self.team_locks,
        )

        self.settled_bets.extend(newly_settled)
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

        if len(eligible) >= self.request.multiple_legs:
            combo = build_valid_combo(eligible, self.request.multiple_legs)

            if combo:
                self._attempt_place_bet(combo)

        # ALWAYS update context
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

            if self.request.min_odds is not None and odds < self.request.min_odds:
                return

            combined_odds *= odds
            selections[match.id] = selection

            if self.request.staking_method == "kelly":
                prob = {
                    "H": match.model_home_prob,
                    "D": match.model_draw_prob,
                    "A": match.model_away_prob,
                }[selection]

                if prob is None:
                    return

                combined_prob *= prob

        stake = calculate_stake(
            self.request,
            self.bankroll,
            combined_odds,
            combined_prob,
        )

        if stake is None or stake <= 0 or stake > self.bankroll:
            return

        bet = Bet(
            matches=[match for match, _ in combo],
            stake=stake,
            combined_odds=combined_odds,
            settles_at=max(match.kickoff for match, _ in combo),
            selections=selections,
        )

        self.active_bets.append(bet)
        self.bankroll -= stake

        for match, _ in combo:
            self.team_locks[match.home_team] = match.id
            self.team_locks[match.away_team] = match.id

    def _final_settlement(self, matches):
        if not matches:
            return

        final_kickoff = matches[-1].kickoff

        self.bankroll, newly_settled = settle_matured_bets(
            self.active_bets,
            final_kickoff,
            self.bankroll,
            self.team_locks,
            settle_all=True,
        )

        self.settled_bets.extend(newly_settled)
        self._update_drawdown()

    # --------------------------------------------------
    # Risk Tracking
    # --------------------------------------------------

    def _update_drawdown(self):
        if self.bankroll > self.peak_bankroll:
            self.peak_bankroll = self.bankroll

        if self.peak_bankroll == 0:
            return
        drawdown = (self.peak_bankroll - self.bankroll) / self.peak_bankroll
        self.max_drawdown = max(self.max_drawdown, drawdown)


def calculate_metrics(settled_bets, starting_bankroll, final_bankroll):
    total_bets = len(settled_bets)
    total_staked = sum(b.stake for b in settled_bets)
    total_profit = sum(b.profit for b in settled_bets)

    total_wins = sum(1 for b in settled_bets if b.is_win)
    total_losses = total_bets - total_wins

    strike_rate = (total_wins / total_bets * 100) if total_bets else 0

    avg_odds = (
        sum(b.combined_odds for b in settled_bets) / total_bets if total_bets else 0
    )

    roi = (
        (final_bankroll - starting_bankroll) / starting_bankroll * 100
        if starting_bankroll
        else 0
    )

    # Streaks
    longest_win_streak = 0
    longest_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0

    for bet in settled_bets:
        if bet.is_win:
            current_win_streak += 1
            current_loss_streak = 0
        else:
            current_loss_streak += 1
            current_win_streak = 0

        longest_win_streak = max(longest_win_streak, current_win_streak)
        longest_loss_streak = max(longest_loss_streak, current_loss_streak)

    return {
        "total_bets": total_bets,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "strike_rate_percent": round(strike_rate, 2),
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
        "average_odds": round(avg_odds, 2),
        "longest_win_streak": longest_win_streak,
        "longest_loss_streak": longest_loss_streak,
        "roi_percent": round(roi, 2),
    }
