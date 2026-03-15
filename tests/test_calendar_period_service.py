import math
import uuid
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.application.calendar_period_service import CalendarPeriodService
from app.domain.simulation.models import SimulationRequest


class FakeMatch:
    def __init__(
        self,
        idx: int,
        kickoff: datetime,
        *,
        league: str = "TestLeague",
        season: str = "2425",
        result: str = "H",
        ppi_diff: float | None = None,
    ):
        self.id = uuid.uuid4()
        self.league = league
        self.season = season
        self.kickoff = kickoff
        self.home_team = f"H{idx}"
        self.away_team = f"A{idx}"

        if result == "H":
            self.home_goals = 1
            self.away_goals = 0
        elif result == "A":
            self.home_goals = 0
            self.away_goals = 1
        else:
            self.home_goals = 1
            self.away_goals = 1

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


def make_custom_periods(*periods):
    if periods:
        return list(periods)
    return [
        {"name": "Weekend", "start_day": "fri", "end_day": "mon"},
        {"name": "Midweek", "start_day": "tue", "end_day": "thu"},
    ]


def make_request(**overrides) -> SimulationRequest:
    base = dict(
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
        period_mode="custom",
        custom_periods=make_custom_periods(),
        reset_bankroll_each_period=False,
        max_candidates_per_period=None,
        rank_by=None,
        rank_order="asc",
        require_full_candidate_count=False,
    )
    base.update(overrides)
    return SimulationRequest(**base)


def _collect_leg_match_ids(result: dict) -> set[str]:
    ids = set()
    for bet in result["bets"]:
        for leg in bet["legs"]:
            ids.add(leg["match_id"])
    return ids


def test_calendar_periods_top_4_smallest_ppidiff_without_rule():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.08),  # Fri
        FakeMatch(2, base + timedelta(days=1), result="H", ppi_diff=0.03),  # Sat
        FakeMatch(3, base + timedelta(days=2), result="H", ppi_diff=0.01),  # Sun
        FakeMatch(4, base + timedelta(days=3), result="H", ppi_diff=0.06),  # Mon
        FakeMatch(5, base + timedelta(days=4), result="H", ppi_diff=0.02),  # Tue
        FakeMatch(6, base + timedelta(days=5), result="H", ppi_diff=0.09),  # Wed
    ]

    request = make_request(
        max_candidates_per_period=4,
        rank_by="PPIDiff",
        rank_order="asc",
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["calendar_periods"] is True
    assert result["total_periods"] == 2
    assert [p["period_label"] for p in result["periods"]] == ["Weekend", "Midweek"]
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

    request = make_request(
        max_candidates_per_period=4,
        rank_by="PPIDiff",
        rank_order="asc",
        require_full_candidate_count=True,
    )

    result = CalendarPeriodService().run(matches, request)

    # Neither weekend (2) nor midweek (1) has 4 candidates, so no bets.
    assert result["total_bets"] == 0
    assert result["final_bankroll"] == 1000


def test_custom_period_fri_to_mon_groups_correctly():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), ppi_diff=0.04),  # Fri
        FakeMatch(2, base + timedelta(days=1), ppi_diff=0.03),  # Sat
        FakeMatch(3, base + timedelta(days=2), ppi_diff=0.02),  # Sun
        FakeMatch(4, base + timedelta(days=3), ppi_diff=0.01),  # Mon
    ]

    request = make_request(
        custom_periods=make_custom_periods(
            {"name": "Weekend", "start_day": "fri", "end_day": "mon"}
        )
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["total_periods"] == 1
    assert result["periods"][0]["period_label"] == "Weekend"
    assert result["periods"][0]["matches_in_period"] == 4
    assert result["total_bets"] == 4


def test_custom_period_tue_to_thu_groups_correctly():
    base = datetime(2025, 1, 7, 15, 0)  # Tuesday

    matches = [
        FakeMatch(1, base + timedelta(days=0), ppi_diff=0.04),  # Tue
        FakeMatch(2, base + timedelta(days=1), ppi_diff=0.03),  # Wed
        FakeMatch(3, base + timedelta(days=2), ppi_diff=0.02),  # Thu
    ]

    request = make_request(
        custom_periods=make_custom_periods(
            {"name": "Midweek", "start_day": "tue", "end_day": "thu"}
        )
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["total_periods"] == 1
    assert result["periods"][0]["period_label"] == "Midweek"
    assert result["periods"][0]["matches_in_period"] == 3
    assert result["total_bets"] == 3


def test_calendar_groups_into_chronological_weekend_midweek_blocks():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0)),  # Fri -> weekend
        FakeMatch(2, base + timedelta(days=1)),  # Sat -> weekend
        FakeMatch(3, base + timedelta(days=4)),  # Tue -> midweek
        FakeMatch(4, base + timedelta(days=5)),  # Wed -> midweek
        FakeMatch(5, base + timedelta(days=7)),  # Fri -> weekend
    ]

    request = make_request()

    result = CalendarPeriodService().run(matches, request)

    assert result["calendar_periods"] is True
    assert result["total_periods"] == 3
    assert [p["period_label"] for p in result["periods"]] == [
        "Weekend",
        "Midweek",
        "Weekend",
    ]


def test_calendar_ranking_only_singles_selects_smallest_ppidiff_per_period():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    weekend_matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.08),
        FakeMatch(2, base + timedelta(days=1), result="H", ppi_diff=0.03),
        FakeMatch(3, base + timedelta(days=2), result="H", ppi_diff=0.01),
        FakeMatch(4, base + timedelta(days=3), result="H", ppi_diff=0.06),
    ]

    midweek_matches = [
        FakeMatch(5, base + timedelta(days=4), result="H", ppi_diff=0.04),
        FakeMatch(6, base + timedelta(days=5), result="H", ppi_diff=0.02),
    ]

    matches = weekend_matches + midweek_matches

    request = make_request(
        selection="H",
        rule_expression=None,
        multiple_legs=1,
        max_candidates_per_period=2,
        rank_by="PPIDiff",
        rank_order="asc",
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["total_bets"] == 4

    expected_ids = {
        str(weekend_matches[2].id),  # 0.01
        str(weekend_matches[1].id),  # 0.03
        str(midweek_matches[1].id),  # 0.02
        str(midweek_matches[0].id),  # 0.04
    }
    actual_ids = _collect_leg_match_ids(result)

    assert actual_ids == expected_ids


def test_calendar_rule_plus_ranking_filters_then_selects_top_matches():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="D", ppi_diff=0.15),  # fails rule
        FakeMatch(2, base + timedelta(days=1), result="D", ppi_diff=0.08),  # qualifies
        FakeMatch(3, base + timedelta(days=2), result="D", ppi_diff=0.03),  # qualifies
        FakeMatch(4, base + timedelta(days=3), result="D", ppi_diff=0.06),  # qualifies
        FakeMatch(5, base + timedelta(days=4), result="D", ppi_diff=0.20),  # fails rule
    ]

    request = make_request(
        selection="D",
        rule_expression="PPIDiff < 0.1",
        multiple_legs=1,
        max_candidates_per_period=2,
        rank_by="PPIDiff",
        rank_order="asc",
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["total_bets"] == 2

    expected_ids = {
        str(matches[2].id),  # 0.03
        str(matches[3].id),  # 0.06
    }
    actual_ids = _collect_leg_match_ids(result)

    assert actual_ids == expected_ids
    assert str(matches[0].id) not in actual_ids
    assert str(matches[4].id) not in actual_ids


def test_calendar_multiple_legs_four_preserves_exact_selected_candidates():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    selected_matches = [
        FakeMatch(
            1,
            base + timedelta(days=0),
            result="D",
            ppi_diff=0.08,
            league="Belgian-Pro-League",
        ),
        FakeMatch(
            2,
            base + timedelta(days=1),
            result="D",
            ppi_diff=0.03,
            league="2-Bundesliga",
        ),
        FakeMatch(
            3, base + timedelta(days=2), result="D", ppi_diff=0.01, league="La-Liga"
        ),
        FakeMatch(
            4, base + timedelta(days=3), result="D", ppi_diff=0.06, league="Serie-B"
        ),
    ]

    extras = [
        FakeMatch(
            5,
            base + timedelta(days=0, hours=1),
            result="D",
            ppi_diff=0.20,
            league="Premier-League",
        ),
        FakeMatch(
            6,
            base + timedelta(days=1, hours=1),
            result="D",
            ppi_diff=0.30,
            league="Championship",
        ),
    ]

    matches = selected_matches + extras

    request = make_request(
        selection="D",
        rule_expression=None,
        multiple_legs=4,
        max_candidates_per_period=4,
        rank_by="PPIDiff",
        rank_order="asc",
        require_full_candidate_count=True,
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["total_bets"] == 1
    assert len(result["bets"][0]["legs"]) == 4

    expected_ids = {str(m.id) for m in selected_matches}
    actual_ids = {leg["match_id"] for leg in result["bets"][0]["legs"]}

    assert actual_ids == expected_ids


def test_calendar_bankroll_carry_forward_vs_reset_per_period():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.01),
        FakeMatch(2, base + timedelta(days=4), result="A", ppi_diff=0.01),
    ]

    request_carry = make_request(
        selection="H",
        multiple_legs=1,
        max_candidates_per_period=1,
        rank_by="PPIDiff",
        rank_order="asc",
        reset_bankroll_each_period=False,
    )

    result_carry = CalendarPeriodService().run(matches, request_carry)

    assert result_carry["total_periods"] == 2
    assert result_carry["periods"][0]["starting_bankroll"] == 1000
    assert result_carry["periods"][0]["final_bankroll"] == 1100
    assert result_carry["periods"][1]["starting_bankroll"] == 1100
    assert result_carry["periods"][1]["final_bankroll"] == 1000
    assert result_carry["final_bankroll"] == 1000

    request_reset = make_request(
        selection="H",
        multiple_legs=1,
        max_candidates_per_period=1,
        rank_by="PPIDiff",
        rank_order="asc",
        reset_bankroll_each_period=True,
    )

    result_reset = CalendarPeriodService().run(matches, request_reset)

    assert result_reset["total_periods"] == 2
    assert result_reset["periods"][0]["starting_bankroll"] == 1000
    assert result_reset["periods"][0]["final_bankroll"] == 1100
    assert result_reset["periods"][1]["starting_bankroll"] == 1000
    assert result_reset["periods"][1]["final_bankroll"] == 900
    assert result_reset["final_bankroll"] == 1000


def test_calendar_require_full_candidate_count_skips_incomplete_period():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.01),
        FakeMatch(2, base + timedelta(days=1), result="H", ppi_diff=0.02),
        FakeMatch(3, base + timedelta(days=4), result="H", ppi_diff=0.03),
    ]

    request = make_request(
        selection="H",
        multiple_legs=4,
        max_candidates_per_period=4,
        rank_by="PPIDiff",
        rank_order="asc",
        require_full_candidate_count=True,
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["total_bets"] == 0
    assert result["final_bankroll"] == 1000
    assert all(period["total_bets"] == 0 for period in result["periods"])


def test_calendar_profit_factor_is_none_when_no_losses_and_result_is_json_safe():
    base = datetime(2025, 1, 3, 15, 0)  # Friday

    matches = [
        FakeMatch(1, base + timedelta(days=0), result="H", ppi_diff=0.01),
        FakeMatch(2, base + timedelta(days=1), result="H", ppi_diff=0.02),
    ]

    request = make_request(
        selection="H",
        multiple_legs=1,
        max_candidates_per_period=1,
        rank_by="PPIDiff",
        rank_order="asc",
    )

    result = CalendarPeriodService().run(matches, request)

    assert result["profit_factor"] is None

    def assert_no_nonfinite(value):
        if isinstance(value, float):
            assert math.isfinite(value)
        elif isinstance(value, dict):
            for v in value.values():
                assert_no_nonfinite(v)
        elif isinstance(value, list):
            for v in value:
                assert_no_nonfinite(v)

    assert_no_nonfinite(result)


def test_overlapping_custom_periods_raise_validation_error():
    with pytest.raises(ValidationError, match="overlap|Overlapping|overlapping"):
        make_request(
            custom_periods=make_custom_periods(
                {"name": "Weekend", "start_day": "fri", "end_day": "mon"},
                {"name": "EarlyWeek", "start_day": "sun", "end_day": "tue"},
            )
        )


def test_duplicate_custom_period_names_raise_validation_error():
    with pytest.raises(ValidationError, match="unique|duplicate|Duplicate"):
        make_request(
            custom_periods=make_custom_periods(
                {"name": "Weekend", "start_day": "fri", "end_day": "mon"},
                {"name": "Weekend", "start_day": "tue", "end_day": "thu"},
            )
        )
