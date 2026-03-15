from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import RuleStrategy


def build_strategy(request: SimulationRequest):
    if not request.selection:
        raise ValueError("selection is required")

    return RuleStrategy(
        rule_expression=request.rule_expression,
        selection=request.selection,
    )
