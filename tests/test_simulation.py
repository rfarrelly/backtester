import uuid
from datetime import datetime

from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import RuleStrategy


class FakeMatch:
    def __init__(
        self,
        *,
        result: str,
        kickoff: datetime,
        home_win_odds: float = 2.0,
        draw_odds: float = 3.5,
        away_win_odds: float = 4.0,
        features: dict | None = None,
    ):
        self.id = uuid.uuid4()
        self.league = "TestLeague"
        self.season = "2425"
        self.kickoff = kickoff
        self.home_team = "Home"
        self.away_team = "Away"
        self.result = result

        if result == "H":
            self.home_goals = 1
            self.away_goals = 0
        elif result == "A":
            self.home_goals = 0
            self.away_goals = 1
        else:
            self.home_goals = 1
            self.away_goals = 1

        self.home_win_odds = home_win_odds
        self.draw_odds = draw_odds
        self.away_win_odds = away_win_odds

        self.model_home_prob = None
        self.model_draw_prob = None
        self.model_away_prob = None

        self.features = features or {}


def make_request(**overrides) -> SimulationRequest:
    base = dict(
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
    base.update(overrides)
    return SimulationRequest(**base)


def test_rule_strategy_without_expression_places_bets_on_all_matches():
    matches = [
        FakeMatch(result="H", kickoff=datetime(2025, 1, 1, 15, 0)),
        FakeMatch(result="A", kickoff=datetime(2025, 1, 2, 15, 0)),
    ]

    request = make_request(selection="H", rule_expression=None)
    strategy = RuleStrategy(rule_expression=None, selection="H")
    engine = SimulationEngine(request, strategy)

    result = engine.run(matches)

    assert result["total_bets"] == 2
    assert len(result["bets"]) == 2


def test_rule_strategy_with_expression_filters_matches():
    matches = [
        FakeMatch(
            result="D",
            kickoff=datetime(2025, 1, 1, 15, 0),
            features={"PPIDiff": 0.05},
        ),
        FakeMatch(
            result="D",
            kickoff=datetime(2025, 1, 2, 15, 0),
            features={"PPIDiff": 0.20},
        ),
    ]

    request = make_request(selection="D", rule_expression="PPIDiff < 0.1")
    strategy = RuleStrategy(rule_expression="PPIDiff < 0.1", selection="D")
    engine = SimulationEngine(request, strategy)

    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert len(result["bets"]) == 1
    assert result["bets"][0]["legs"][0]["selection"] == "D"


def test_fixed_singles_all_wins():
    matches = [
        FakeMatch(result="H", kickoff=datetime(2025, 1, 1, 15, 0)),
        FakeMatch(result="H", kickoff=datetime(2025, 1, 2, 15, 0)),
    ]

    request = make_request(selection="H", fixed_stake=100)
    strategy = RuleStrategy(rule_expression=None, selection="H")
    engine = SimulationEngine(request, strategy)

    result = engine.run(matches)

    assert result["total_bets"] == 2
    assert result["total_wins"] == 2
    assert result["final_bankroll"] > 1000


def test_fixed_singles_all_losses():
    matches = [
        FakeMatch(result="A", kickoff=datetime(2025, 1, 1, 15, 0)),
        FakeMatch(result="A", kickoff=datetime(2025, 1, 2, 15, 0)),
    ]

    request = make_request(selection="H", fixed_stake=100)
    strategy = RuleStrategy(rule_expression=None, selection="H")
    engine = SimulationEngine(request, strategy)

    result = engine.run(matches)

    assert result["total_bets"] == 2
    assert result["total_wins"] == 0
    assert result["final_bankroll"] == 800


def test_multiple_legs_two_builds_accumulator():
    matches = [
        FakeMatch(result="H", kickoff=datetime(2025, 1, 1, 15, 0)),
        FakeMatch(result="H", kickoff=datetime(2025, 1, 1, 16, 0)),
    ]

    request = make_request(selection="H", fixed_stake=100, multiple_legs=2)
    strategy = RuleStrategy(rule_expression=None, selection="H")
    engine = SimulationEngine(request, strategy)

    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert len(result["bets"][0]["legs"]) == 2
    assert result["bets"][0]["is_win"] is True


def test_min_odds_filters_out_short_prices():
    matches = [
        FakeMatch(
            result="H",
            kickoff=datetime(2025, 1, 1, 15, 0),
            home_win_odds=1.5,
        ),
        FakeMatch(
            result="H",
            kickoff=datetime(2025, 1, 2, 15, 0),
            home_win_odds=2.2,
        ),
    ]

    request = make_request(selection="H", fixed_stake=100, min_odds=2.0)
    strategy = RuleStrategy(rule_expression=None, selection="H")
    engine = SimulationEngine(request, strategy)

    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert len(result["bets"]) == 1
