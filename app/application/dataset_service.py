from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.application.calendar_period_service import CalendarPeriodService
from app.application.in_memory_dataset_loader import load_matches_from_csv
from app.application.strategy_factory import build_strategy
from app.application.walk_forward_service import WalkForwardService
from app.domain.simulation.config import SimulationConfig
from app.domain.simulation.engine import SimulationEngine
from app.infrastructure.persistence_models.dataset import Dataset
from app.infrastructure.persistence_models.simulation_run import SimulationRun
from app.infrastructure.repositories.simulation_run_repository import (
    SimulationRunRepository,
)

UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "app/data/uploads"))


@dataclass(frozen=True)
class DatasetIntrospection:
    columns: list[str]
    inferred_types: dict[str, str]
    sample_rows: list[dict[str, Any]]


class DatasetService:
    def __init__(self, db):
        self.db = db

    def save_upload(
        self, *, owner_user_id, filename: str, file_bytes: bytes
    ) -> Dataset:
        dataset = Dataset(
            owner_user_id=owner_user_id,
            original_filename=filename,
            stored_path="",
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)

        user_dir = UPLOAD_ROOT / str(owner_user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        stored_path = user_dir / f"{dataset.id}.csv"
        stored_path.write_bytes(file_bytes)

        dataset.stored_path = str(stored_path)
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def list_datasets(self, *, owner_user_id):
        return (
            self.db.query(Dataset)
            .filter(Dataset.owner_user_id == owner_user_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )

    def get_owned_dataset(self, *, dataset_id, owner_user_id) -> Dataset:
        ds = (
            self.db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .filter(Dataset.owner_user_id == owner_user_id)
            .first()
        )
        if not ds:
            raise ValueError("Dataset not found")
        return ds

    def delete_dataset(self, *, dataset_id, owner_user_id):
        ds = self.get_owned_dataset(dataset_id=dataset_id, owner_user_id=owner_user_id)

        try:
            p = Path(ds.stored_path)
            if p.exists():
                p.unlink()
        except Exception:
            pass

        self.db.delete(ds)
        self.db.commit()

    def introspect(
        self, *, dataset: Dataset, sample_size: int = 25
    ) -> DatasetIntrospection:
        path = Path(dataset.stored_path)
        if not path.exists():
            raise ValueError("Dataset file missing on disk")

        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []

            rows: list[dict[str, Any]] = []
            for i, row in enumerate(reader):
                rows.append(row)
                if i + 1 >= sample_size:
                    break

        inferred = self._infer_types(columns, rows)
        return DatasetIntrospection(
            columns=columns,
            inferred_types=inferred,
            sample_rows=rows,
        )

    def _infer_types(
        self, columns: list[str], rows: list[dict[str, Any]]
    ) -> dict[str, str]:
        def infer_one(values: list[str | None]) -> str:
            cleaned = [
                v.strip() for v in values if v is not None and str(v).strip() != ""
            ]
            if not cleaned:
                return "empty"

            def is_int(x: str) -> bool:
                try:
                    int(x)
                    return True
                except Exception:
                    return False

            def is_float(x: str) -> bool:
                try:
                    float(x)
                    return True
                except Exception:
                    return False

            if all(is_int(v) for v in cleaned):
                return "int"
            if all(is_float(v) for v in cleaned):
                return "float"

            lowered = [v.lower() for v in cleaned]
            if all(v in {"true", "false", "0", "1", "yes", "no"} for v in lowered):
                return "bool"

            if all(
                ("-" in v or "/" in v) and any(ch.isdigit() for ch in v)
                for v in cleaned
            ):
                return "date_like"

            return "string"

        out: dict[str, str] = {}
        for col in columns:
            vals = [r.get(col) for r in rows]
            out[col] = infer_one(vals)
        return out

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

    def _validate_walk_forward_request(self, request):
        if not request.walk_forward:
            return

        if not request.train_window_matches or not request.test_window_matches:
            raise ValueError(
                "train_window_matches and test_window_matches are required when walk_forward=True"
            )

        if request.train_window_matches <= 0 or request.test_window_matches <= 0:
            raise ValueError("walk-forward window sizes must be positive")

        if request.step_matches is not None and request.step_matches <= 0:
            raise ValueError("step_matches must be positive")

    def _validate_calendar_request(self, request):
        if request.period_mode == "none":
            return

        if request.period_mode == "custom":
            if not request.custom_periods:
                raise ValueError("custom_periods is required when period_mode='custom'")

    def _sanitize_json_value(self, value):
        if isinstance(value, float):
            if not math.isfinite(value):
                return None
            return value

        if isinstance(value, dict):
            return {k: self._sanitize_json_value(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._sanitize_json_value(v) for v in value]

        return value

    def _sanitize_result_for_storage(self, result: dict):
        return self._sanitize_json_value(result)

    def simulate_dataset(
        self,
        *,
        dataset_id,
        owner_user_id,
        mapping,
        request,
        persist: bool = True,
        runs_repo=None,
    ):
        ds = self.get_owned_dataset(
            dataset_id=dataset_id,
            owner_user_id=owner_user_id,
        )

        matches = load_matches_from_csv(
            ds.stored_path,
            mapping=mapping,
            default_league=request.league,
            default_season=request.season,
        )

        matches = self._filter_matches_for_request(matches, request)

        return self.simulate_loaded_matches(
            dataset=ds,
            owner_user_id=owner_user_id,
            mapping=mapping,
            request=request,
            matches=matches,
            persist=persist,
            runs_repo=runs_repo,
        )

    def get_distinct_values(
        self,
        *,
        dataset_id,
        owner_user_id,
        column: str,
        limit: int = 500,
    ):
        ds = self.get_owned_dataset(
            dataset_id=dataset_id,
            owner_user_id=owner_user_id,
        )

        path = Path(ds.stored_path)
        if not path.exists():
            raise ValueError("Dataset file missing on disk")

        values = set()

        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames or column not in reader.fieldnames:
                raise ValueError(f"Column '{column}' not found in dataset")

            for row in reader:
                raw = row.get(column)
                if raw is None:
                    continue

                value = str(raw).strip()
                if not value:
                    continue

                values.add(value)

                if len(values) >= limit:
                    break

        return sorted(values)

    def simulate_loaded_matches(
        self,
        *,
        dataset,
        owner_user_id,
        mapping,
        request,
        matches,
        persist: bool = True,
        runs_repo=None,
    ):
        self._validate_walk_forward_request(request)
        self._validate_calendar_request(request)

        config = SimulationConfig.from_request(request)

        if config.walk_forward_enabled:
            result = WalkForwardService().run(matches, config)
        elif config.period_mode != "none":
            result = CalendarPeriodService().run(matches, config)
        else:
            strategy = build_strategy(config)
            engine = SimulationEngine(config, strategy)
            result = engine.run(matches)

        if not persist:
            return {
                "run_id": None,
                "dataset_id": str(dataset.id),
                **result,
            }

        if runs_repo is None:
            runs_repo = SimulationRunRepository(self.db)

        sanitized_result = self._sanitize_result_for_storage(result)

        run = SimulationRun(
            owner_user_id=owner_user_id,
            dataset_id=dataset.id,
            mapping_json=mapping.model_dump(),
            request_json=request.model_dump(),
            result_json=sanitized_result,
        )

        run = runs_repo.create(run)

        return {
            "run_id": str(run.id),
            "dataset_id": str(dataset.id),
            **result,
        }
