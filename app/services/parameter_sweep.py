import copy
import itertools

from app.simulation.engine import SimulationEngine


class ParameterSweep:
    def __init__(self, matches, base_request, strategy_factory, param_grid):
        """
        matches: list of match objects
        base_request: SimulationRequest
        strategy_factory: callable that builds strategy from params
        param_grid: dict like {"min_edge": [0.01, 0.05], "window": [3,5]}
        """
        self.matches = matches
        self.base_request = base_request
        self.strategy_factory = strategy_factory
        self.param_grid = param_grid

    def _generate_param_combinations(self):
        keys = self.param_grid.keys()
        values = self.param_grid.values()

        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))

    def rank_by_roi(self):
        results = self.run()
        return sorted(results, key=lambda x: x["roi_percent"], reverse=True)

    def run(self):
        results = []

        for params in self._generate_param_combinations():
            request_copy = copy.deepcopy(self.base_request)

            strategy = self.strategy_factory(**params)

            engine = SimulationEngine(
                matches=self.matches,
                request=request_copy,
                strategy=strategy,
            )

            simulation_result = engine.run()

            results.append(
                {
                    **params,
                    "final_bankroll": simulation_result["final_bankroll"],
                    "roi_percent": simulation_result["roi_percent"],
                    "total_bets": simulation_result["total_bets"],
                }
            )

        return results
