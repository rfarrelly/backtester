from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import (
    AlwaysHomeStrategy,
    EdgeStrategy,
    RuleStrategy,
)


def build_strategy(request: SimulationRequest):
    if request.strategy_type == "home":
        return AlwaysHomeStrategy()

    if request.strategy_type == "edge":
        return EdgeStrategy(selection=request.selection, min_edge=request.min_edge)

    if request.strategy_type == "rules":
        if not request.rule_expression:
            raise ValueError("rule_expression is required for rules strategy")
        if not request.selection:
            raise ValueError("selection is required for rules strategy")
        return RuleStrategy(
            rule_expression=request.rule_expression, selection=request.selection
        )

    raise ValueError("Unsupported strategy")
