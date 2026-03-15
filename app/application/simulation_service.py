from app.application.strategy_factory import build_strategy
from app.domain.simulation.config import SimulationConfig
from app.domain.simulation.engine import SimulationEngine
from app.infrastructure.repositories.match_repository import MatchRepository


class SimulationService:
    def __init__(self, db):
        self.repo = MatchRepository(db)

    def run(self, request):
        config = SimulationConfig.from_request(request)
        matches = self.repo.get_matches(
            season=config.season,
            league=config.league,
            leagues=config.leagues,
        )

        strategy = build_strategy(config)
        engine = SimulationEngine(config, strategy)
        return engine.run(matches)
