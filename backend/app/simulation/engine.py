from itertools import combinations, groupby
from operator import attrgetter

from app.models.match import Match
from app.models.odds import Odds
from sqlalchemy.orm import Session

from .models import SimulationRequest


class Bet:
    def __init__(self, matches, stake, combined_odds, settles_at, selections):
        self.matches = matches  # list[Match]
        self.stake = stake
        self.combined_odds = combined_odds
        self.settles_at = settles_at
        self.selections = selections  # {match_id: "H"/"D"/"A"}


def run_simulation(db, request):
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

    equity_curve = []
    peak = bankroll
    max_drawdown = 0

    total_bets = 0

    for kickoff, group in groupby(matches, key=attrgetter("kickoff")):
        batch = list(group)

        # -------------------
        # 1️⃣ Settle matured bets
        # -------------------

        for bet in active_bets[:]:
            if bet.settles_at <= kickoff:
                win = True
                for match in bet.matches:
                    if match.result != bet.selections[match.id]:
                        win = False
                        break

                if win:
                    bankroll += bet.stake * bet.combined_odds
                else:
                    # stake already deducted
                    pass

                # unlock teams
                for match in bet.matches:
                    team_locks.pop(match.home_team, None)
                    team_locks.pop(match.away_team, None)

                active_bets.remove(bet)

                # drawdown tracking
                equity_curve.append(bankroll)
                if bankroll > peak:
                    peak = bankroll
                drawdown = (peak - bankroll) / peak
                max_drawdown = max(max_drawdown, drawdown)

        # -------------------
        # 2️⃣ Filter eligible matches
        # -------------------
        eligible = []

        for match in batch:
            if match.home_team not in team_locks and match.away_team not in team_locks:
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
        combined_odds = 1
        combined_prob = 1
        selections = {}

        for match in combo:
            odds = {
                "H": match.odds.home_win,
                "D": match.odds.draw,
                "A": match.odds.away_win,
            }[request.selection]

            if request.min_odds and odds < request.min_odds:
                continue

            combined_odds *= odds
            selections[match.id] = request.selection

            # Kelly support (if model probs exist)
            if request.staking_method == "kelly":
                prob = {
                    "H": match.odds.model_home_prob,
                    "D": match.odds.model_draw_prob,
                    "A": match.odds.model_away_prob,
                }[request.selection]

                if prob is None:
                    combined_prob = None
                else:
                    combined_prob *= prob

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
        win = all(match.result == bet.selections[match.id] for match in bet.matches)

        if win:
            bankroll += bet.stake * bet.combined_odds
        else:
            # stake already deducted
            pass

        active_bets.remove(bet)

        equity_curve.append(bankroll)
        if bankroll > peak:
            peak = bankroll
        drawdown = (peak - bankroll) / peak
        max_drawdown = max(max_drawdown, drawdown)

    roi = (bankroll - request.starting_bankroll) / request.starting_bankroll * 100

    return {
        "bets": active_bets,
        "final_bankroll": round(bankroll, 2),
        "roi_percent": round(roi, 2),
        "max_drawdown_percent": round(max_drawdown * 100, 2),
        "total_bets": total_bets,
    }
