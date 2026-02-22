import uuid
from datetime import datetime

from app.simulation.engine import run_simulation
from app.simulation.models import SimulationRequest

# -------------------------
# Fake ORM Models
# -------------------------


class FakeOdds:
    def __init__(self, home, draw, away):
        self.home_win = home
        self.draw = draw
        self.away_win = away

        # Kelly fields (unused here)
        self.model_home_prob = None
        self.model_draw_prob = None
        self.model_away_prob = None


class FakeMatch:
    def __init__(self, home, away, kickoff, result):
        self.id = uuid.uuid4()
        self.league = "TestLeague"
        self.season = "2025"
        self.home_team = home
        self.away_team = away
        self.kickoff = kickoff
        self.home_goals = 2
        self.away_goals = 0
        self.result = result
        self.odds = FakeOdds(2.0, 3.5, 4.0)


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
    kickoff1 = datetime(2025, 1, 1, 15, 0)
    kickoff2 = datetime(2025, 1, 2, 15, 0)
    kickoff3 = datetime(2025, 1, 3, 15, 0)
    kickoff4 = datetime(2025, 1, 4, 15, 0)

    matches = sorted(
        [
            FakeMatch("A", "B", kickoff1, "H"),
            FakeMatch("C", "D", kickoff2, "H"),
            FakeMatch("E", "F", kickoff3, "H"),
            FakeMatch("G", "H", kickoff4, "H"),
        ],
        key=lambda m: m.kickoff,
    )

    db = FakeDB(matches)

    request = SimulationRequest(
        league="TestLeague",
        season="2025",
        starting_bankroll=1000,
        selection="H",
        staking_method="fixed",
        fixed_stake=100,
        percent_stake=None,
        kelly_fraction=None,
        multiple_legs=1,
        min_odds=None,
    )

    result = run_simulation(db, request)
    print(result)

    assert result["total_bets"] == 4
    assert result["final_bankroll"] == 1400
    assert result["roi_percent"] == 40.0
    assert result["max_drawdown_percent"] == 0.0
