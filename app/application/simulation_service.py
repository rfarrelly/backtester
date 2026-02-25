from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import AlwaysHomeStrategy, EdgeStrategy
from app.infrastructure.repositories.match_repository import MatchRepository


def build_strategy_from_request(request: SimulationRequest):
    if request.strategy_type == "home":
        return AlwaysHomeStrategy()

    if request.strategy_type == "edge":
        return EdgeStrategy(
            selection=request.selection,
            min_edge=request.min_edge,
        )

    raise ValueError("Unsupported strategy")


def simulate_strategy(db, request):
    strategy = build_strategy_from_request(request)

    repo = MatchRepository(db)

    matches = repo.get_matches(
        league=request.league,
        season=request.season,
    )

    engine = SimulationEngine(
        matches=matches,
        request=request,
        strategy=strategy,
    )

    return engine.run()
