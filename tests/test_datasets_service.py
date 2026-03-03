import uuid
from pathlib import Path

from app.application.dataset_service import DatasetService
from app.infrastructure.persistence_models.dataset import Dataset


def test_introspect_returns_columns_rows_and_types(tmp_path, db_session):
    # 1) Create temp CSV
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "Date,Home,Away,FTHG,FTAG,PPIDiff\n"
        "2023-08-01,A,B,2,1,0.05\n"
        "2023-08-02,C,D,0,0,0.10\n",
        encoding="utf-8",
    )

    # 2) Insert dataset row
    user_id = uuid.uuid4()
    ds = Dataset(
        owner_user_id=user_id,
        original_filename="sample.csv",
        stored_path=str(csv_path),
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    # 3) Introspect
    service = DatasetService(db_session)
    info = service.introspect(dataset=ds, sample_size=2)

    assert info.columns == ["Date", "Home", "Away", "FTHG", "FTAG", "PPIDiff"]
    assert len(info.sample_rows) == 2
    assert info.sample_rows[0]["Home"] == "A"

    # types are heuristic; check key ones
    assert info.inferred_types["FTHG"] in ("int", "float")
    assert info.inferred_types["PPIDiff"] == "float"


def test_delete_dataset_removes_file_and_row(tmp_path, db_session):
    csv_path = tmp_path / "to_delete.csv"
    csv_path.write_text("a,b\n1,2\n", encoding="utf-8")

    user_id = uuid.uuid4()
    ds = Dataset(
        owner_user_id=user_id,
        original_filename="to_delete.csv",
        stored_path=str(csv_path),
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    assert Path(ds.stored_path).exists()

    service = DatasetService(db_session)
    service.delete_dataset(dataset_id=ds.id, owner_user_id=user_id)

    assert not Path(csv_path).exists()

    # row removed
    found = db_session.query(Dataset).filter(Dataset.id == ds.id).first()
    assert found is None
