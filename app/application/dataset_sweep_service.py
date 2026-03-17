import itertools
from typing import Any

from app.application.dataset_service import DatasetService
from app.application.in_memory_dataset_loader import load_matches_from_csv
from app.infrastructure.persistence_models.dataset import Dataset
from app.infrastructure.persistence_models.simulation_run import SimulationRun
from app.infrastructure.repositories.simulation_run_repository import (
    SimulationRunRepository,
)


class DatasetSweepService:
    def __init__(self, db):
        self.db = db
        self.dataset_service = DatasetService(db)

    def _generate_param_combinations(self, grid: dict[str, list[Any]]):
        if not grid:
            yield {}
            return

        keys = list(grid.keys())
        values = [grid[k] for k in keys]

        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))

    def _filter_matches_for_request(self, matches, request):
        filtered = matches

        if request.season:
            season = request.season.strip()
            filtered = [m for m in filtered if m.season and m.season.strip() == season]

        if request.leagues:
            requested_leagues = {
                league.strip()
                for league in request.leagues
                if league and league.strip()
            }
            filtered = [
                m
                for m in filtered
                if m.league and m.league.strip() in requested_leagues
            ]
        elif request.league:
            requested_league = request.league.strip()
            filtered = [
                m for m in filtered if m.league and m.league.strip() == requested_league
            ]

        return filtered

    @staticmethod
    def _build_sweep_row(
        *, params: dict[str, Any], run_id: str | None, simulation_result: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            # New field for analytics UI.
            "parameters": params,
            # Backward-compatible alias for older frontend/tests.
            "params": params,
            "run_id": run_id,
            "roi_percent": simulation_result.get("roi_percent"),
            "final_bankroll": simulation_result.get("final_bankroll"),
            "total_bets": simulation_result.get("total_bets"),
            "total_wins": simulation_result.get("total_wins"),
            "total_losses": simulation_result.get("total_losses"),
            "max_drawdown_percent": simulation_result.get("max_drawdown_percent"),
            "strike_rate_percent": simulation_result.get("strike_rate_percent"),
            "profit_factor": simulation_result.get("profit_factor"),
            "average_odds": simulation_result.get("average_odds"),
            "total_profit": simulation_result.get("total_profit"),
        }

    def run_sweep(
        self,
        *,
        dataset_id,
        owner_user_id,
        mapping,
        base_request,
        grid: dict[str, list[Any]],
        persist_runs: bool = True,
    ):
        ds: Dataset = self.dataset_service.get_owned_dataset(
            dataset_id=dataset_id,
            owner_user_id=owner_user_id,
        )

        all_matches = load_matches_from_csv(
            ds.stored_path,
            mapping=mapping,
            default_league=base_request.league,
            default_season=base_request.season,
        )

        runs_repo = SimulationRunRepository(self.db)
        rows: list[dict[str, Any]] = []

        for params in self._generate_param_combinations(grid):
            variant_request = base_request.model_copy(update=params)
            matches = self._filter_matches_for_request(all_matches, variant_request)

            simulation_result = self.dataset_service.simulate_loaded_matches(
                dataset=ds,
                owner_user_id=owner_user_id,
                mapping=mapping,
                request=variant_request,
                matches=matches,
                persist=False,
                runs_repo=None,
            )

            run_id = None
            if persist_runs:
                sanitized_result = self.dataset_service._sanitize_result_for_storage(
                    simulation_result
                )

                run = SimulationRun(
                    owner_user_id=owner_user_id,
                    dataset_id=ds.id,
                    mapping_json=mapping.model_dump(),
                    request_json=variant_request.model_dump(),
                    result_json=sanitized_result,
                )
                run = runs_repo.create(run)
                run_id = str(run.id)

            rows.append(
                self._build_sweep_row(
                    params=params,
                    run_id=run_id,
                    simulation_result=simulation_result,
                )
            )

        rows.sort(
            key=lambda row: (row.get("roi_percent") is None, row.get("roi_percent", 0)),
            reverse=True,
        )

        parameter_names = list(grid.keys())

        return {
            "parameter_names": parameter_names,
            "row_count": len(rows),
            "rows": rows,
            # Backward-compatible aliases for current frontend/tests.
            "total_variants": len(rows),
            "results": rows,
        }
