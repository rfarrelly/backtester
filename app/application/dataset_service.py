from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.infrastructure.persistence_models.dataset import Dataset

# Stored relative to project root (works both on host + in docker-compose)
UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "app/data/uploads"))


@dataclass(frozen=True)
class DatasetIntrospection:
    columns: list[str]
    inferred_types: dict[str, str]
    sample_rows: list[dict[str, Any]]


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    def save_upload(
        self, *, owner_user_id, filename: str, file_bytes: bytes
    ) -> Dataset:
        """Persist metadata in DB and store the CSV bytes on disk."""

        # Create DB row first so we have an id for the stored filename.
        ds = Dataset(
            owner_user_id=owner_user_id,
            original_filename=filename,
            stored_path="",
        )

        self.db.add(ds)
        self.db.commit()
        self.db.refresh(ds)

        user_dir = UPLOAD_ROOT / str(owner_user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        stored_path = user_dir / f"{ds.id}.csv"
        stored_path.write_bytes(file_bytes)

        ds.stored_path = str(stored_path)
        self.db.add(ds)
        self.db.commit()
        self.db.refresh(ds)

        return ds

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

    def introspect(
        self, *, dataset: Dataset, sample_size: int = 25
    ) -> DatasetIntrospection:
        path = Path(dataset.stored_path)
        if not path.exists():
            raise ValueError("Dataset file missing")

        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames or []

            sample_rows: list[dict[str, Any]] = []
            for i, row in enumerate(reader):
                sample_rows.append(row)
                if i + 1 >= sample_size:
                    break

        inferred = self._infer_types(columns, sample_rows)
        return DatasetIntrospection(
            columns=columns, inferred_types=inferred, sample_rows=sample_rows
        )

    def _infer_types(
        self, columns: list[str], rows: list[dict[str, Any]]
    ) -> dict[str, str]:
        def infer_one(values: list[str | None]) -> str:
            cleaned = [
                str(v).strip() for v in values if v is not None and str(v).strip() != ""
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

            # lightweight date-ish heuristic
            if all(
                any(ch.isdigit() for ch in v) and ("-" in v or "/" in v)
                for v in cleaned
            ):
                return "date_like"

            return "string"

        out: dict[str, str] = {}
        for col in columns:
            vals = [r.get(col) for r in rows]
            out[col] = infer_one(vals)

        return out
