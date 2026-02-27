from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")

from sqlalchemy.orm import Session

from app.application.parameter_sweep_service import ParameterSweep
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import AlwaysHomeStrategy, EdgeStrategy
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.match_repository import MatchRepository


def main():
    db: Session = SessionLocal()

    base_request = SimulationRequest(
        league="Premier-League",
        season="2526",
        strategy_type="home",  # change to "edge" when probs exist
        selection="H",
        staking_method="fixed",
        fixed_stake=100,
        starting_bankroll=1000,
        multiple_legs=2,
        min_odds=None,
        min_edge=0.0,  # overridden in sweep
        percent_stake=None,
        kelly_fraction=None,
    )

    # Load matches once
    repo = MatchRepository(db)
    matches = repo.get_matches(
        league=base_request.league,
        season=base_request.season,
    )

    # Build strategies for each param combo
    def strategy_factory(**params):
        # params may include min_edge, etc.
        if base_request.strategy_type == "home":
            return AlwaysHomeStrategy()

        if base_request.strategy_type == "edge":
            selection = params.get("selection", base_request.selection)
            min_edge = params.get("min_edge", base_request.min_edge)
            return EdgeStrategy(selection=selection, min_edge=min_edge)

        raise ValueError("Unsupported strategy_type in sweep")

    sweep = ParameterSweep(
        matches=matches,
        base_request=base_request,
        strategy_factory=strategy_factory,
        param_grid={
            "min_edge": [0.00, 0.02, 0.05, 0.08, 0.10],
        },
    )

    ranked = sweep.rank_by_roi()

    for row in ranked[:20]:
        print(
            f"min_edge={row['min_edge']:.2f}  ROI={row['roi_percent']:.2f}%  "
            f"DD={row['max_drawdown_percent']:.2f}%  SR={row['strike_rate_percent']:.2f}%  "
            f"AvgOdds={row['average_odds']:.2f}  PF={row['profit_factor']}  "
            f"bets={row['total_bets']}  final={row['final_bankroll']}"
        )


if __name__ == "__main__":
    main()
