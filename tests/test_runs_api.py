import uuid

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from api.main import app
from app.infrastructure.db.session import get_db
from app.infrastructure.persistence_models.dataset import Dataset
from app.infrastructure.persistence_models.simulation_run import SimulationRun


@pytest.fixture
def client(db_session):
    """
    Provides a TestClient with dependency overrides:
    - get_db -> uses sqlite db_session fixture
    - get_current_user -> returns a fake user object
    """

    class FakeUser:
        def __init__(self, user_id):
            self.id = user_id

    user_id = uuid.uuid4()

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return FakeUser(user_id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        c._test_user_id = user_id  # attach for convenience
        yield c

    app.dependency_overrides.clear()


def _insert_dataset(db_session, owner_user_id, path="dummy.csv"):
    ds = Dataset(
        owner_user_id=owner_user_id,
        original_filename="dummy.csv",
        stored_path=path,
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)
    return ds


def _insert_run(db_session, owner_user_id, dataset_id, roi=12.34):
    run = SimulationRun(
        owner_user_id=owner_user_id,
        dataset_id=dataset_id,
        mapping_json={"home_team_col": "HomeTeam"},
        request_json={"selection": "H", "staking_method": "fixed"},
        result_json={
            "roi_percent": roi,
            "final_bankroll": 1111.0,
            "total_bets": 3,
            "max_drawdown_percent": 5.5,
            "bets": [],
            "equity_curve": [],
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_list_runs_returns_only_current_user_runs(client, db_session):
    user_id = client._test_user_id
    other_user_id = uuid.uuid4()

    ds1 = _insert_dataset(db_session, owner_user_id=user_id, path="a.csv")
    ds2 = _insert_dataset(db_session, owner_user_id=other_user_id, path="b.csv")

    run_owned = _insert_run(
        db_session, owner_user_id=user_id, dataset_id=ds1.id, roi=10.0
    )
    _insert_run(db_session, owner_user_id=other_user_id, dataset_id=ds2.id, roi=99.0)

    resp = client.get("/runs")
    assert resp.status_code == 200

    runs = resp.json()
    assert isinstance(runs, list)
    assert len(runs) == 1
    assert runs[0]["run_id"] == str(run_owned.id)
    assert runs[0]["dataset_id"] == str(ds1.id)
    assert runs[0]["roi_percent"] == 10.0


def test_get_run_returns_full_payload_for_owner(client, db_session):
    user_id = client._test_user_id
    ds = _insert_dataset(db_session, owner_user_id=user_id, path="a.csv")
    run = _insert_run(db_session, owner_user_id=user_id, dataset_id=ds.id, roi=7.0)

    resp = client.get(f"/runs/{run.id}")
    assert resp.status_code == 200

    data = resp.json()
    assert data["run_id"] == str(run.id)
    assert data["dataset_id"] == str(ds.id)
    assert "mapping" in data and isinstance(data["mapping"], dict)
    assert "request" in data and isinstance(data["request"], dict)
    assert "result" in data and isinstance(data["result"], dict)
    assert data["result"]["roi_percent"] == 7.0


def test_get_run_404_for_non_owner(client, db_session):
    user_id = client._test_user_id
    other_user_id = uuid.uuid4()

    ds = _insert_dataset(db_session, owner_user_id=other_user_id, path="b.csv")
    run = _insert_run(
        db_session, owner_user_id=other_user_id, dataset_id=ds.id, roi=55.0
    )

    resp = client.get(f"/runs/{run.id}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Run not found"


def test_delete_run_deletes_for_owner(client, db_session):
    user_id = client._test_user_id
    ds = _insert_dataset(db_session, owner_user_id=user_id, path="a.csv")
    run = _insert_run(db_session, owner_user_id=user_id, dataset_id=ds.id, roi=1.0)

    resp = client.delete(f"/runs/{run.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "deleted"
    assert body["run_id"] == str(run.id)

    # ensure gone
    resp2 = client.get(f"/runs/{run.id}")
    assert resp2.status_code == 404
