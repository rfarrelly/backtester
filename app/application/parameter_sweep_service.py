import itertools
from copy import deepcopy
from typing import Any, Callable

from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest


class ParameterSweep:
    def __init__(self, matches, base_request, strategy_factory, param_grid):
        """
        matches: list of match objects
        base_request: SimulationRequest
        strategy_factory: callable that builds strategy from params
        param_grid: dict like {"min_odds": [2.0, 3.0], "multiple_legs": [1, 2]}
        """
        self.matches = matches
        self.base_request = base_request
        self.strategy_factory = strategy_factory
        self.param_grid = param_grid

    def _generate_param_combinations(self):
        keys = list(self.param_grid.keys())
        values = [self.param_grid[key] for key in keys]

        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))

    def rank_by_roi(self):
        result = self.run()
        return sorted(
            result["rows"],
            key=lambda row: (row.get("roi_percent") is None, row.get("roi_percent", 0)),
            reverse=True,
        )

    def run(self):
        rows: list[dict[str, Any]] = []

        for params in self._generate_param_combinations():
            request_copy = self.base_request.model_copy(update=params)
            strategy = self.strategy_factory(**params)

            engine = SimulationEngine(request_copy, strategy)
            simulation_result = engine.run(self.matches)

            rows.append(self._build_sweep_row(params=params, result=simulation_result))

        rows.sort(
            key=lambda row: (row.get("roi_percent") is None, row.get("roi_percent", 0)),
            reverse=True,
        )

        return {
            "parameter_names": list(self.param_grid.keys()),
            "row_count": len(rows),
            "rows": rows,
            # Backward-compatible aliases for older consumers.
            "total_variants": len(rows),
            "results": rows,
        }

    @staticmethod
    def _build_sweep_row(
        params: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            # New field for analytics UI.
            "parameters": deepcopy(params),
            # Backward-compatible alias for existing frontend/tests.
            "params": deepcopy(params),
            "run_id": result.get("run_id"),
            "roi_percent": result.get("roi_percent"),
            "total_profit": result.get("total_profit"),
            "total_bets": result.get("total_bets"),
            "total_wins": result.get("total_wins"),
            "total_losses": result.get("total_losses"),
            "strike_rate_percent": result.get("strike_rate_percent"),
            "max_drawdown_percent": result.get("max_drawdown_percent"),
            "profit_factor": result.get("profit_factor"),
            "final_bankroll": result.get("final_bankroll"),
            "average_odds": result.get("average_odds"),
        }


class ParameterSweepService:
    """Generic parameter sweep runner for request-like simulation workflows."""

    def run(
        self,
        *,
        base_request: SimulationRequest,
        sweep_parameters: dict[str, list[Any]],
        run_variant: Callable[[SimulationRequest], dict[str, Any]],
    ) -> dict[str, Any]:
        parameter_names = list(sweep_parameters.keys())

        if not parameter_names:
            result = run_variant(base_request)
            rows = [self._build_sweep_row(parameters={}, result=result)]
            return {
                "parameter_names": [],
                "row_count": 1,
                "rows": rows,
                # Backward-compatible aliases.
                "total_variants": 1,
                "results": rows,
            }

        value_lists = [sweep_parameters[name] for name in parameter_names]
        rows: list[dict[str, Any]] = []

        for combination in itertools.product(*value_lists):
            variant_request = self._build_variant_request(
                base_request=base_request,
                parameter_names=parameter_names,
                parameter_values=combination,
            )
            result = run_variant(variant_request)
            parameters = dict(zip(parameter_names, combination))
            rows.append(self._build_sweep_row(parameters=parameters, result=result))

        rows.sort(
            key=lambda row: (row.get("roi_percent") is None, row.get("roi_percent", 0)),
            reverse=True,
        )

        return {
            "parameter_names": parameter_names,
            "row_count": len(rows),
            "rows": rows,
            # Backward-compatible aliases.
            "total_variants": len(rows),
            "results": rows,
        }

    @staticmethod
    def _build_variant_request(
        *,
        base_request: SimulationRequest,
        parameter_names: list[str],
        parameter_values: tuple[Any, ...],
    ) -> SimulationRequest:
        payload = deepcopy(base_request.model_dump())
        for name, value in zip(parameter_names, parameter_values):
            payload[name] = value
        return SimulationRequest(**payload)

    @staticmethod
    def _build_sweep_row(
        *,
        parameters: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "parameters": deepcopy(parameters),
            "params": deepcopy(parameters),
            "run_id": result.get("run_id"),
            "roi_percent": result.get("roi_percent"),
            "total_profit": result.get("total_profit"),
            "total_bets": result.get("total_bets"),
            "total_wins": result.get("total_wins"),
            "total_losses": result.get("total_losses"),
            "strike_rate_percent": result.get("strike_rate_percent"),
            "max_drawdown_percent": result.get("max_drawdown_percent"),
            "profit_factor": result.get("profit_factor"),
            "final_bankroll": result.get("final_bankroll"),
            "average_odds": result.get("average_odds"),
        }
