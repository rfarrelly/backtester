from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import (
    AlwaysHomeStrategy,
    EdgeStrategy,
    RuleStrategy,
)
from app.infrastructure.repositories.match_repository import MatchRepository


class SimulationService:
    def __init__(self, db):
        self.repo = MatchRepository(db)

    def _build_strategy(self, request: SimulationRequest):
        if request.strategy_type == "home":
            return AlwaysHomeStrategy()

        if request.strategy_type == "edge":
            return EdgeStrategy(
                selection=request.selection,
                min_edge=request.min_edge,
            )

        if request.strategy_type == "rules":
            return RuleStrategy(
                rule_expression=request.rule_expression,
                selection=request.selection or "H",
            )
        if request.strategy_type == "rules" and not request.rule_expression:
            raise ValueError("rule_expression is required for rules strategy")

        raise ValueError("Unsupported strategy")

    def run(self, request: SimulationRequest):
        strategy = self._build_strategy(request)

        matches = self.repo.get_matches(
            league=request.league,
            season=request.season,
        )

        engine = SimulationEngine(request, strategy)

        return engine.run(matches)
