from app.application.strategy_factory import build_strategy
from app.domain.simulation.engine import SimulationEngine
from app.infrastructure.repositories.match_repository import MatchRepository


class SimulationService:
    def __init__(self, db):
        self.repo = MatchRepository(db)

    def run(self, request):
        matches = self.repo.get_matches(
            season=request.season,
            league=request.league,
            leagues=request.leagues,
        )

        strategy = build_strategy(request)
        engine = SimulationEngine(request, strategy)
        return engine.run(matches)
