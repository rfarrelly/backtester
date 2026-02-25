from app.simulation.engine import SimulationEngine
from app.simulation.models import SimulationRequest
from app.simulation.strategy import AlwaysHomeStrategy, EdgeStrategy


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
    engine = SimulationEngine(db, request, strategy)
    return engine.run()
