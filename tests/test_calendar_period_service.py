import uuid
from datetime import datetime, timedelta

from app.application.calendar_period_service import CalendarPeriodService
from app.domain.simulation.models import SimulationRequest


class FakeMatch:
    def __init__(
        self,
        idx: int,
        kickoff: datetime,
        result: str = "H",
        ppi_diff: float | None = None,
    ):
        self.id = uuid.uuid4()
        self.league = "TestLeague"
        self.season = "2425"
        self.kickoff = kickoff
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
        if ppi_diff is not None:
            self.features["PPIDiff"] = ppi_diff


def test_calendar_periods_top_4_smallest_ppidiff_without_rule():
    # Fri, Sat, Sun, Mon, Tue, Wed
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.08),  # Fri
        FakeMatch(2, base + timedelta(days=1), result="H", ppi_diff=0.03),  # Sat
        FakeMatch(3, base + timedelta(days=2), result="H", ppi_diff=0.01),  # Sun
        FakeMatch(4, base + timedelta(days=3), result="H", ppi_diff=0.06),  # Mon
        FakeMatch(5, base + timedelta(days=4), result="H", ppi_diff=0.02),  # Tue
        FakeMatch(6, base + timedelta(days=5), result="H", ppi_diff=0.09),  # Wed
    ]

    request = SimulationRequest(
        league="TestLeague",
        leagues=None,
        season="2425",
        strategy_type="rules",
        selection="H",
        rule_expression=None,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
        min_edge=None,
        walk_forward=False,
        train_window_matches=None,
        test_window_matches=None,
        step_matches=None,
        period_mode="custom_day_groups",
        custom_periods={
            "weekend": [4, 5, 6, 0],
            "midweek": [1, 2, 3],
        },
        reset_bankroll_each_period=False,
        max_candidates_per_period=4,
        rank_by="PPIDiff",
        rank_order="asc",
        require_full_candidate_count=False,
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["calendar_periods"] is True
    assert result["total_periods"] == 2
    # weekend has 4 candidates, midweek has 2 candidates; all are H winners
    assert result["total_bets"] == 6
    assert result["final_bankroll"] > 1000


def test_calendar_periods_require_full_candidate_count_skips_small_period():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.08),  # Fri
        FakeMatch(2, base + timedelta(days=1), result="H", ppi_diff=0.03),  # Sat
        FakeMatch(3, base + timedelta(days=4), result="H", ppi_diff=0.02),  # Tue
    ]

    request = SimulationRequest(
        league="TestLeague",
        leagues=None,
        season="2425",
        strategy_type="rules",
        selection="H",
        rule_expression=None,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
        min_edge=None,
        walk_forward=False,
        train_window_matches=None,
        test_window_matches=None,
        step_matches=None,
        period_mode="custom_day_groups",
        custom_periods={
            "weekend": [4, 5, 6, 0],
            "midweek": [1, 2, 3],
        },
        reset_bankroll_each_period=False,
        max_candidates_per_period=4,
        rank_by="PPIDiff",
        rank_order="asc",
        require_full_candidate_count=True,
    )

    result = CalendarPeriodService().run(matches, request)

    # Neither weekend (2) nor midweek (1) has 4 candidates, so no bets.
    assert result["total_bets"] == 0
    assert result["final_bankroll"] == 1000
