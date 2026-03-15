from datetime import datetime, timedelta

from app.application.walk_forward_service import WalkForwardService
from app.domain.simulation.models import SimulationRequest


class FakeMatch:
    def __init__(self, idx, result="H"):
        self.id = idx
        self.league = "TestLeague"
        self.season = "2025"
        self.kickoff = datetime(2025, 1, 1) + timedelta(days=idx)
        self.home_team = f"H{idx}"
        self.away_team = f"A{idx}"
        self.home_goals = 1
        self.away_goals = 0
        self.result = result
        self.home_win_odds = 2.0
        self.draw_odds = 3.5
        self.away_win_odds = 4.0
        self.model_home_prob = None
        self.model_draw_prob = None
        self.model_away_prob = None
        self.features = {}


def test_walk_forward_runs_multiple_segments():
    matches = [FakeMatch(i, result="H") for i in range(30)]

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        selection="H",
        rule_expression=None,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
        walk_forward=True,
        train_window_matches=10,
        test_window_matches=5,
        step_matches=5,
    )

    result = WalkForwardService().run(matches, request)

    assert result["walk_forward"] is True
    assert result["total_segments"] == 4
    assert len(result["segments"]) == 4
    assert result["total_bets"] == 20
