import uuid
from datetime import datetime
from pathlib import Path

from app.application.dataset_mapping import DatasetMapping
from app.application.dataset_service import DatasetService
from app.domain.simulation.models import SimulationRequest
from app.infrastructure.persistence_models.dataset import Dataset


class FakeRun:
    def __init__(self):
        self.id = uuid.uuid4()


class FakeRunRepo:
    def __init__(self):
        self.created = []

    def create(self, run):
        self.created.append(run)
        run.id = uuid.uuid4()
        return run


def test_simulate_dataset_persists_run_record(tmp_path, db_session):
    # Create tiny CSV on disk
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "League,Season,Date,HomeTeam,AwayTeam,FTR,B365CH,B365CD,B365CA\n"
        "TestLeague,2025,2025-01-01,A,B,H,2.0,3.5,4.0\n",
        encoding="utf-8",
    )

    owner_id = uuid.uuid4()

    # Insert dataset row
    ds = Dataset(
        owner_user_id=owner_id,
        original_filename="sample.csv",
        stored_path=str(csv_path),
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    mapping = DatasetMapping(
        home_team_col="HomeTeam",
        away_team_col="AwayTeam",
        date_col="Date",
        time_col=None,
        league_col="League",
        season_col="Season",
        result_col="FTR",
        odds_home_col="B365CH",
        odds_draw_col="B365CD",
        odds_away_col="B365CA",
        feature_cols=[],
    )

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="home",
        selection=None,
        rule_expression=None,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
    )

    fake_repo = FakeRunRepo()
    service = DatasetService(db_session)

    result = service.simulate_dataset(
        dataset_id=ds.id,
        owner_user_id=owner_id,
        mapping=mapping,
        request=request,
        persist=True,
        runs_repo=fake_repo,
    )

    assert "run_id" in result
    assert result["total_bets"] == 1
    assert len(fake_repo.created) == 1
    created_run = fake_repo.created[0]
    assert created_run.owner_user_id == owner_id
    assert created_run.dataset_id == ds.id
    assert created_run.result_json["total_bets"] == 1


def test_simulate_dataset_without_persist_does_not_create_run(tmp_path, db_session):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "League,Season,Date,HomeTeam,AwayTeam,FTR,B365CH,B365CD,B365CA\n"
        "TestLeague,2025,2025-01-01,A,B,H,2.0,3.5,4.0\n",
        encoding="utf-8",
    )

    owner_id = uuid.uuid4()

    ds = Dataset(
        owner_user_id=owner_id,
        original_filename="sample.csv",
        stored_path=str(csv_path),
    )
    db_session.add(ds)
    db_session.commit()
    db_session.refresh(ds)

    mapping = DatasetMapping(
        home_team_col="HomeTeam",
        away_team_col="AwayTeam",
        date_col="Date",
        time_col=None,
        league_col="League",
        season_col="Season",
        result_col="FTR",
        odds_home_col="B365CH",
        odds_draw_col="B365CD",
        odds_away_col="B365CA",
        feature_cols=[],
    )

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="home",
        selection=None,
        rule_expression=None,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
    )

    fake_repo = FakeRunRepo()
    service = DatasetService(db_session)

    result = service.simulate_dataset(
        dataset_id=ds.id,
        owner_user_id=owner_id,
        mapping=mapping,
        request=request,
        persist=False,
        runs_repo=fake_repo,
    )

    assert result["run_id"] is None
    assert result["dataset_id"] == str(ds.id)
    assert result["total_bets"] == 1
    assert len(fake_repo.created) == 0
