from app.models.match import Match
from app.models.odds import Odds
from sqlalchemy.orm import Session

from .models import SimpleBacktestRequest


def run_simple_backtest(db: Session, request: SimpleBacktestRequest):
    query = (
        db.query(Match, Odds)
        .join(Odds, Odds.match_id == Match.id)
        .filter(Match.league == request.league)
        .filter(Match.season == request.season)
        .order_by(Match.kickoff.asc())
    )

    total_profit = 0.0
    total_bets = 0
    wins = 0
    losses = 0
    results = []

    for match, odds in query.all():
        odds_map = {
            "H": odds.home_win,
            "D": odds.draw,
            "A": odds.away_win,
        }

        selected_odds = odds_map.get(request.selection)

        if selected_odds is None:
            continue

        if request.min_odds and selected_odds < request.min_odds:
            continue

        total_bets += 1

        if match.result == request.selection:
            profit = (selected_odds - 1) * request.stake
            wins += 1
        else:
            profit = -request.stake
            losses += 1

        total_profit += profit

        results.append(
            {
                "match_id": str(match.id),
                "kickoff": match.kickoff.isoformat(),
                "home": match.home_team,
                "away": match.away_team,
                "odds": selected_odds,
                "profit": round(profit, 2),
            }
        )

    roi = (total_profit / (total_bets * request.stake)) * 100 if total_bets else 0

    return {
        "total_bets": total_bets,
        "wins": wins,
        "losses": losses,
        "profit": round(total_profit, 2),
        "roi_percent": round(roi, 2),
        "details": results,
    }
