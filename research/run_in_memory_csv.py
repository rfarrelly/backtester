from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")

from app.application.dataset_mapping import DatasetMapping
from app.application.in_memory_dataset_loader import load_matches_from_csv
from app.application.simulation_service import build_strategy
from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest


def main():
    mapping = DatasetMapping(
        league_col="League",
        season_col="Season",
        date_col="Date",
        time_col=None,
        home_team_col="Home",
        away_team_col="Away",
        home_goals_col="FTHG",
        away_goals_col="FTAG",
        result_col="result",
        feature_cols=[
            "HomeTeamTotalPPG",
            "AwayTeamTotalPPG",
            "HomeTeamPPI",
            "AwayTeamPPI",
            "PPIDiff",
        ],
    )

    request = SimulationRequest(
        league="Premier-League",
        season="2023-2024",
        strategy_type="rules",
        selection="D",
        rule_expression="HomeTeamPPI > 0 and AwayTeamPPI > 0 and AwayTeamPPI > HomeTeamPPI and 0 < PPIDiff < 0.1",
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
        min_edge=None,
    )

    matches = load_matches_from_csv(
        "app/data/sample_ppi.csv",
        mapping=mapping,
        default_league="Premier-League",
        default_season="2023-2024",
    )

    # IMPORTANT: file contains multiple leagues/seasons; filter to request scope
    matches_all = matches
    matches = [
        m
        for m in matches_all
        if m.league == request.league and m.season == request.season
    ]

    print(f"Loaded total matches: {len(matches_all)}")
    print(f"Filtered matches for {request.league} {request.season}: {len(matches)}")

    leagues = sorted({m.league for m in matches_all})
    seasons = sorted({m.season for m in matches_all})
    print(
        "Leagues in file (sample):", leagues[:10], ("..." if len(leagues) > 10 else "")
    )
    print(
        "Seasons in file (sample):", seasons[:10], ("..." if len(seasons) > 10 else "")
    )

    strategy = build_strategy(request)
    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    print("\nSUMMARY")
    print(
        f"ROI={result['roi_percent']:.2f}%  final={result['final_bankroll']}  "
        f"bets={result['total_bets']}  wins={result['total_wins']}  "
        f"SR={result['strike_rate_percent']:.2f}%  DD={result['max_drawdown_percent']:.2f}%"
    )

    print("\nFIRST 10 BETS")
    for i, bet in enumerate(result["bets"][:10], start=1):
        # bet is a dict if your engine serializes
        if isinstance(bet, dict):
            leg0 = bet["legs"][0]
            kickoff = leg0["kickoff"]
            home = leg0["home_team"]
            away = leg0["away_team"]
            sel = leg0["selection"]
            res = leg0["result"]
            profit = bet["profit"]
            is_win = bet["is_win"]

            feats = leg0.get("features", {})
            print(
                f"{i:02d} {kickoff}  {home} vs {away}  sel={sel}  result={res}  "
                f"win={is_win}  profit={profit}  "
                f"PPI(H/A)={feats.get('HomeTeamPPI')}/{feats.get('AwayTeamPPI')}  "
                f"PPIDiff={feats.get('PPIDiff')}"
            )
        else:
            # object mode (if you run engine without serialization)
            m0 = bet.matches[0]
            print(
                f"{i:02d} {m0.kickoff}  {m0.home_team} vs {m0.away_team}  "
                f"win={bet.is_win}  profit={bet.profit}"
            )


if __name__ == "__main__":
    main()
