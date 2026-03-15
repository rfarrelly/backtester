from app.domain.simulation.config import SimulationConfig
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import RuleStrategy


def build_strategy(config: SimulationConfig | SimulationRequest):
    if isinstance(config, SimulationRequest):
        config = SimulationConfig.from_request(config)

    if not config.selection:
        raise ValueError("selection is required")

    return RuleStrategy(
        rule_expression=config.rule_expression,
        selection=config.selection,
    )
