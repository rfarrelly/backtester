import uuid
from pathlib import Path

from app.application.dataset_mapping import DatasetMapping
from app.application.dataset_sweep_service import DatasetSweepService
from app.domain.simulation.models import SimulationRequest
from app.infrastructure.persistence_models.dataset import Dataset


def _make_dataset(db_session, tmp_path: Path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "League,Season,Date,HomeTeam,AwayTeam,FTR,B365CH,B365CD,B365CA,PPIDiff\n"
        "TestLeague,2425,2025-01-03,A,B,H,2.0,3.5,4.0,0.01\n"
        "TestLeague,2425,2025-01-04,C,D,H,2.0,3.5,4.0,0.05\n"
        "TestLeague,2425,2025-01-07,E,F,H,2.0,3.5,4.0,0.10\n",
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
    return owner_id, ds


def _mapping():
    return DatasetMapping(
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
        feature_cols=["PPIDiff"],
    )


def _base_request():
    return SimulationRequest(
        league="TestLeague",
        leagues=None,
        season="2425",
        selection="H",
        rule_expression=None,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
        walk_forward=False,
        train_window_matches=None,
        test_window_matches=None,
        step_matches=None,
        period_mode="none",
        custom_periods=None,
        reset_bankroll_each_period=False,
        max_candidates_per_period=None,
        rank_by=None,
        rank_order="asc",
        require_full_candidate_count=False,
    )


def test_dataset_sweep_single_parameter(db_session, tmp_path):
    owner_id, ds = _make_dataset(db_session, tmp_path)
    service = DatasetSweepService(db_session)

    result = service.run_sweep(
        dataset_id=ds.id,
        owner_user_id=owner_id,
        mapping=_mapping(),
        base_request=_base_request(),
        grid={"multiple_legs": [1, 2]},
        persist_runs=False,
    )

    assert result["parameter_names"] == ["multiple_legs"]
    assert result["row_count"] == 2
    assert len(result["rows"]) == 2

    # Backward-compatible aliases remain available.
    assert result["total_variants"] == 2
    assert len(result["results"]) == 2

    assert {r["parameters"]["multiple_legs"] for r in result["rows"]} == {1, 2}
    assert {r["params"]["multiple_legs"] for r in result["rows"]} == {1, 2}


def test_dataset_sweep_two_parameter_grid(db_session, tmp_path):
    owner_id, ds = _make_dataset(db_session, tmp_path)
    service = DatasetSweepService(db_session)

    result = service.run_sweep(
        dataset_id=ds.id,
        owner_user_id=owner_id,
        mapping=_mapping(),
        base_request=_base_request(),
        grid={
            "multiple_legs": [1, 2],
            "fixed_stake": [50, 100],
        },
        persist_runs=False,
    )

    assert result["parameter_names"] == ["multiple_legs", "fixed_stake"]
    assert result["row_count"] == 4
    assert len(result["rows"]) == 4

    params_seen = {
        (r["parameters"]["multiple_legs"], r["parameters"]["fixed_stake"])
        for r in result["rows"]
    }
    assert params_seen == {(1, 50), (1, 100), (2, 50), (2, 100)}


def test_dataset_sweep_persists_runs(db_session, tmp_path):
    owner_id, ds = _make_dataset(db_session, tmp_path)
    service = DatasetSweepService(db_session)

    result = service.run_sweep(
        dataset_id=ds.id,
        owner_user_id=owner_id,
        mapping=_mapping(),
        base_request=_base_request(),
        grid={"multiple_legs": [1, 2]},
        persist_runs=True,
    )

    assert result["row_count"] == 2
    assert all(r["run_id"] is not None for r in result["rows"])


def test_dataset_sweep_rows_include_flat_metrics(db_session, tmp_path):
    owner_id, ds = _make_dataset(db_session, tmp_path)
    service = DatasetSweepService(db_session)

    result = service.run_sweep(
        dataset_id=ds.id,
        owner_user_id=owner_id,
        mapping=_mapping(),
        base_request=_base_request(),
        grid={"multiple_legs": [1]},
        persist_runs=False,
    )

    row = result["rows"][0]
    assert "parameters" in row
    assert "params" in row
    assert "roi_percent" in row
    assert "total_profit" in row
    assert "total_bets" in row
    assert "total_wins" in row
    assert "total_losses" in row
    assert "strike_rate_percent" in row
    assert "max_drawdown_percent" in row
    assert "profit_factor" in row
    assert "final_bankroll" in row
