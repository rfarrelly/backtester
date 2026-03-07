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
        c._test_user_id = user_id
        yield c

    app.dependency_overrides.clear()


def test_export_run_bets_csv(client, db_session):
    user_id = client._test_user_id

    ds = Dataset(
        owner_user_id=user_id,
        original_filename="dummy.csv",
        stored_path="dummy.csv",
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    run = SimulationRun(
        owner_user_id=user_id,
        dataset_id=ds.id,
        mapping_json={"home_team_col": "HomeTeam"},
        request_json={"strategy_type": "home"},
        result_json={
            "bets": [
                {
                    "stake": 100.0,
                    "combined_odds": 2.0,
                    "is_win": True,
                    "profit": 100.0,
                    "return_amount": 200.0,
                    "settled_at": "2025-01-01T15:00:00",
                    "legs": [
                        {
                            "match_id": "m1",
                            "kickoff": "2025-01-01T15:00:00",
                            "home_team": "A",
                            "away_team": "B",
                            "result": "H",
                            "selection": "H",
                            "odds": 2.0,
                            "implied_prob": 0.5,
                            "model_prob": None,
                            "edge": None,
                        }
                    ],
                }
            ]
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    resp = client.get(f"/runs/{run.id}/export/bets.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment;" in resp.headers["content-disposition"]

    body = resp.text
    assert "run_id,bet_index,leg_index" in body
    assert str(run.id) in body
    assert "A,B,H,H,2.0" in body or "A,B,H,H,2" in body
