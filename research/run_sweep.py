from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import EdgeStrategy
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.repositories.match_repository import (
    MatchRepository,
)
from app.services.parameter_sweep import ParameterSweep


def edge_strategy_factory(min_edge):
    return EdgeStrategy(
        selection="H",
        min_edge=min_edge,
    )


def main():
    db = SessionLocal()

    repo = MatchRepository(db)

    request = SimulationRequest(
        league="EPL",
        season=2023,
        starting_bankroll=1000,
        staking_method="flat",
        flat_stake=10,
        multiple_legs=1,
    )

    matches = repo.get_matches(
        league=request.league,
        season=request.season,
    )

    param_grid = {
        "min_edge": [0.01, 0.03, 0.05, 0.07, 0.1],
    }

    sweep = ParameterSweep(
        matches=matches,
        base_request=request,
        strategy_factory=edge_strategy_factory,
        param_grid=param_grid,
    )

    results = sweep.rank_by_roi()

    for r in results:
        print(r)


if __name__ == "__main__":
    main()
