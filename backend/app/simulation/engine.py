from itertools import combinations, groupby
from operator import attrgetter

from app.models.match import Match
from app.models.odds import Odds
from sqlalchemy.orm import Session

from .models import SimulationRequest


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


def run_simulation(db, request, strategy):
    settled_bets = []

    matches = (
        db.query(Match)
        .join(Match.odds)
        .filter(Match.league == request.league)
        .filter(Match.season == request.season)
        .order_by(Match.kickoff.asc())
        .all()
    )

    bankroll = request.starting_bankroll
    active_bets = []
    team_locks = {}
    max_drawdown = 0
    total_bets = 0

    for kickoff, group in groupby(matches, key=attrgetter("kickoff")):
        batch = list(group)

        # -------------------
        # 1️⃣ Settle matured bets
        # -------------------

        for bet in active_bets[:]:
            if bet.settles_at <= kickoff:
                is_win = all(
                    match.result == bet.selections[match.id] for match in bet.matches
                )

                if is_win:
                    return_amount = bet.stake * bet.combined_odds
                else:
                    return_amount = 0

                profit = return_amount - bet.stake
                bankroll += return_amount

                settled_bets.append(
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

        # -------------------
        # 2️⃣ Filter eligible matches
        # -------------------
        eligible = []

        for match in batch:
            # Team lock check
            if match.home_team in team_locks or match.away_team in team_locks:
                continue

            # Strategy decision
            decision = strategy.evaluate(match, context={})

            if not decision.place_bet:
                continue

            # Attach decision to match temporarily
            match._strategy_selection = decision.selection

            eligible.append(match)

        if len(eligible) < request.multiple_legs:
            continue

        # -------------------
        # 3️⃣ Build first valid combo only
        # -------------------
        combo = None

        for candidate in combinations(eligible, request.multiple_legs):
            teams = set()
            valid = True

            for match in candidate:
                if match.home_team in teams or match.away_team in teams:
                    valid = False
                    break
                teams.add(match.home_team)
                teams.add(match.away_team)

            if valid:
                combo = candidate
                break

        if not combo:
            continue

        # -------------------
        # 4️⃣ Calculate combined odds + probabilities
        # -------------------
        # -------------------

        combined_odds = 1
        combined_prob = 1
        selections = {}

        for match in combo:
            selection = match._strategy_selection

            odds = {
                "H": match.odds.home_win,
                "D": match.odds.draw,
                "A": match.odds.away_win,
            }[selection]

            if request.min_odds and odds < request.min_odds:
                combined_odds = None
                break

            combined_odds *= odds
            selections[match.id] = selection

            # Kelly support
            if request.staking_method == "kelly":
                prob = {
                    "H": match.odds.model_home_prob,
                    "D": match.odds.model_draw_prob,
                    "A": match.odds.model_away_prob,
                }[selection]

                if prob is None:
                    combined_prob = None
                else:
                    combined_prob *= prob

        if combined_odds is None:
            continue

        # -------------------
        # 5️⃣ Stake Calculation
        # -------------------
        stake = 0

        if request.staking_method == "fixed":
            stake = request.fixed_stake

        elif request.staking_method == "percent":
            stake = bankroll * request.percent_stake

        elif request.staking_method == "kelly":
            if combined_prob is None:
                continue

            b = combined_odds - 1
            f = (b * combined_prob - (1 - combined_prob)) / b

            if f <= 0:
                continue

            stake = bankroll * f * request.kelly_fraction

        if stake <= 0 or stake > bankroll:
            continue

        # -------------------
        # 6️⃣ Place Bet
        # -------------------
        bet = Bet(
            matches=combo,
            stake=stake,
            combined_odds=combined_odds,
            settles_at=max(m.kickoff for m in combo),
            selections=selections,
        )

        active_bets.append(bet)
        bankroll -= stake
        total_bets += 1

        # lock teams
        for match in combo:
            team_locks[match.home_team] = match.id
            team_locks[match.away_team] = match.id

    # Final settlement of remaining bets
    for bet in active_bets[:]:
        is_win = all(match.result == bet.selections[match.id] for match in bet.matches)

        if is_win:
            return_amount = bet.stake * bet.combined_odds
        else:
            return_amount = 0

        profit = return_amount - bet.stake
        bankroll += return_amount

        settled_bets.append(
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

    metrics = calculate_metrics(
        settled_bets,
        request.starting_bankroll,
        bankroll,
    )

    return {
        "bets": settled_bets,
        "final_bankroll": round(bankroll, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        **metrics,
    }


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
