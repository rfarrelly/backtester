import uuid
from datetime import datetime

from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import (
    AlwaysHomeStrategy,
    EdgeStrategy,
    RuleStrategy,
)


class FakeMatch:
    def __init__(self, home, away, kickoff, result, model_home=None):
        self.id = uuid.uuid4()
        self.league = "TestLeague"
        self.season = "2025"
        self.home_team = home
        self.away_team = away
        self.kickoff = kickoff
        self.home_goals = 2
        self.away_goals = 0
        self.result = result

        # flat odds fields (domain-style)
        self.home_win_odds = 2.0
        self.draw_odds = 3.5
        self.away_win_odds = 4.0

        # flat model prob fields (domain-style)
        self.model_home_prob = model_home
        self.model_draw_prob = None
        self.model_away_prob = None


def _is_win(bet):
    """Support both object and dict bet outputs."""
    return bet["is_win"] if isinstance(bet, dict) else bet.is_win


def test_fixed_singles_all_wins():
    strategy = AlwaysHomeStrategy()

    matches = sorted(
        [
            FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H"),
            FakeMatch("C", "D", datetime(2025, 1, 2, 15, 0), "H"),
            FakeMatch("E", "F", datetime(2025, 1, 3, 15, 0), "H"),
            FakeMatch("G", "H", datetime(2025, 1, 4, 15, 0), "H"),
        ],
        key=lambda m: m.kickoff,
    )

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="home",
        selection=None,
        min_edge=None,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 4
    assert result["final_bankroll"] == 1400
    assert result["roi_percent"] == 40.0
    assert result["max_drawdown_percent"] == 0.0
    assert len(result["bets"]) == 4
    assert all(_is_win(b) for b in result["bets"])
    assert result["total_wins"] == 4
    assert result["total_losses"] == 0
    assert result["strike_rate_percent"] == 100.0
    assert result["total_profit"] == 400
    assert result["average_odds"] == 2.0
    assert result["longest_win_streak"] == 4


def test_edge_strategy_places_bet():
    matches = [FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H", model_home=0.6)]

    strategy = EdgeStrategy(selection="H", min_edge=0.05)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="edge",
        selection="H",
        min_edge=0.05,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1100


def test_edge_strategy_blocks_bet_when_edge_too_small():
    matches = [FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H", model_home=0.6)]

    strategy = EdgeStrategy(selection="H", min_edge=0.2)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="edge",
        selection="H",
        min_edge=0.2,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 0
    assert result["final_bankroll"] == 1000


def test_kelly_single_win():
    matches = [FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H", model_home=0.6)]

    strategy = EdgeStrategy(selection="H", min_edge=0.0)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="edge",
        selection="H",
        min_edge=0.0,
        starting_bankroll=1000,
        staking_method="kelly",
        fixed_stake=None,
        percent_stake=None,
        kelly_fraction=1.0,  # full Kelly
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1200.0
    assert result["total_profit"] == 200.0
    assert result["roi_percent"] == 20.0


def test_two_leg_accumulator_all_wins():
    matches = sorted(
        [
            FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H"),
            FakeMatch("C", "D", datetime(2025, 1, 1, 15, 0), "H"),
        ],
        key=lambda m: m.kickoff,
    )

    strategy = AlwaysHomeStrategy()

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="home",
        selection=None,
        min_edge=None,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=2,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1300.0
    assert result["total_profit"] == 300.0
    assert result["roi_percent"] == 30.0


def test_rule_strategy_places_bet_when_true():
    """
    Rule: home_points > away_points
    Build history where Team A has points, Team B has none.
    Then target match A vs B should trigger a bet.
    """
    # History kickoffs (strictly before target)
    h1 = datetime(2025, 1, 1, 12, 0)
    h2 = datetime(2025, 1, 2, 12, 0)

    # Team A gets points (win as home)
    # Team B gets no points (loss as home)
    history = [
        FakeMatch("A", "X", h1, "H"),  # A win -> +3
        FakeMatch("B", "Y", h2, "A"),  # B loss -> +0
    ]

    target = FakeMatch("A", "B", datetime(2025, 1, 3, 15, 0), "H")

    matches = sorted(history + [target], key=lambda m: m.kickoff)

    strategy = RuleStrategy(rule_expression="home_points > away_points", selection="H")

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="rules",
        selection="H",
        rule_expression="home_points > away_points",
        min_edge=None,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1100.0
    assert result["total_wins"] == 1


def test_rule_strategy_blocks_bet_when_false():
    """
    Rule: home_points > away_points
    Build history where Team A has no points, Team B has points.
    Target match A vs B should NOT trigger a bet.
    """
    h1 = datetime(2025, 1, 1, 12, 0)
    h2 = datetime(2025, 1, 2, 12, 0)

    # Team A gets no points (loss as home)
    # Team B gets points (win as home)
    history = [
        FakeMatch("A", "X", h1, "A"),  # A loss -> +0
        FakeMatch("B", "Y", h2, "H"),  # B win -> +3
    ]

    target = FakeMatch("A", "B", datetime(2025, 1, 3, 15, 0), "H")

    matches = sorted(history + [target], key=lambda m: m.kickoff)

    strategy = RuleStrategy(rule_expression="home_points > away_points", selection="H")

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="rules",
        selection="H",
        rule_expression="home_points > away_points",
        min_edge=None,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 0
    assert result["final_bankroll"] == 1000.0


def test_rule_strategy_supports_abs():
    history = [
        FakeMatch("A", "X", datetime(2025, 1, 1, 12, 0), "H"),  # A +3
        FakeMatch("B", "Y", datetime(2025, 1, 2, 12, 0), "D"),  # B +1
    ]
    target = FakeMatch("A", "B", datetime(2025, 1, 3, 15, 0), "H")
    matches = sorted(history + [target], key=lambda m: m.kickoff)

    strategy = RuleStrategy(rule_expression="abs(points_diff) >= 2", selection="H")

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        strategy_type="rules",
        selection="H",
        rule_expression="abs(points_diff) >= 2",
        min_edge=None,
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
