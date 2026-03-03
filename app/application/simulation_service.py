from strategy_factory import build_strategy

from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.rules import RuleCompileError
from app.domain.simulation.strategy import (
    AlwaysHomeStrategy,
    EdgeStrategy,
    RuleStrategy,
)
from app.infrastructure.repositories.match_repository import MatchRepository


class SimulationService:
    def __init__(self, db):
        self.repo = MatchRepository(db)

    def run(self, request: SimulationRequest):
        strategy = build_strategy(request)

        matches = self.repo.get_matches(
            league=request.league,
            season=request.season,
        )

        engine = SimulationEngine(request, strategy)

        return engine.run(matches)
