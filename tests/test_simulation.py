import uuid
from datetime import datetime

from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest
from app.domain.simulation.strategy import AlwaysHomeStrategy, EdgeStrategy

# -------------------------
# Fake Domain Fields
# -------------------------


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

        # Direct domain-style fields
        self.home_win_odds = 2.0
        self.draw_odds = 3.5
        self.away_win_odds = 4.0

        self.model_home_prob = model_home
        self.model_draw_prob = None
        self.model_away_prob = None


# -------------------------
# Fake DB Layer
# -------------------------


class FakeQuery:
    def __init__(self, matches):
        self.matches = matches

    def join(self, *_):
        return self

    def filter(self, *_):
        return self

    def order_by(self, *_):
        return self

    def all(self):
        return self.matches


class FakeDB:
    def __init__(self, matches):
        self.matches = matches

    def query(self, *_):
        return FakeQuery(self.matches)


# -------------------------
# Deterministic Test
# -------------------------


def test_fixed_singles_all_wins():
    strategy = AlwaysHomeStrategy()

    matches = [
        FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H"),
        FakeMatch("C", "D", datetime(2025, 1, 2, 15, 0), "H"),
        FakeMatch("E", "F", datetime(2025, 1, 3, 15, 0), "H"),
        FakeMatch("G", "H", datetime(2025, 1, 4, 15, 0), "H"),
    ]

    db = FakeDB(matches)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
        strategy_type="home",
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 4
    assert result["final_bankroll"] == 1400
    assert result["roi_percent"] == 40.0
    assert result["max_drawdown_percent"] == 0.0
    assert len(result["bets"]) == 4
    assert all(b.is_win for b in result["bets"])
    assert result["total_wins"] == 4
    assert result["total_losses"] == 0
    assert result["strike_rate_percent"] == 100.0
    assert result["total_profit"] == 400
    assert result["average_odds"] == 2.0
    assert result["longest_win_streak"] == 4


def test_edge_strategy_places_bet():
    matches = [FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H", model_home=0.6)]

    db = FakeDB(matches)

    strategy = EdgeStrategy(selection="H", min_edge=0.05)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
        strategy_type="edge",
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1100


def test_edge_strategy_blocks_bet_when_edge_too_small():
    matches = [FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H", model_home=0.6)]

    db = FakeDB(matches)

    strategy = EdgeStrategy(selection="H", min_edge=0.2)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
        strategy_type="edge",
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 0
    assert result["final_bankroll"] == 1000


def test_kelly_single_win():
    matches = [FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H", model_home=0.6)]

    db = FakeDB(matches)

    strategy = EdgeStrategy(selection="H", min_edge=0.0)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        starting_bankroll=1000,
        staking_method="kelly",
        fixed_stake=None,
        percent_stake=None,
        kelly_fraction=1.0,  # full Kelly
        multiple_legs=1,
        min_odds=None,
        strategy_type="edge",
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1200.0
    assert result["total_profit"] == 200.0
    assert result["roi_percent"] == 20.0


def test_two_leg_accumulator_all_wins():
    matches = [
        FakeMatch("A", "B", datetime(2025, 1, 1, 15, 0), "H"),
        FakeMatch("C", "D", datetime(2025, 1, 1, 15, 0), "H"),
    ]

    db = FakeDB(matches)

    strategy = AlwaysHomeStrategy()

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        starting_bankroll=1000,
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=2,
        min_odds=None,
        strategy_type="home",
    )

    engine = SimulationEngine(request, strategy)
    result = engine.run(matches)

    assert result["total_bets"] == 1
    assert result["final_bankroll"] == 1300.0
    assert result["total_profit"] == 300.0
    assert result["roi_percent"] == 30.0
