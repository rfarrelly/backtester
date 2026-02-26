from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Match:
    id: UUID
    league: str
    season: str
    kickoff: datetime

    home_team: str
    away_team: str

    home_goals: int
    away_goals: int
    result: str  # H, D, A

    home_win_odds: float
    draw_odds: float
    away_win_odds: float

    model_home_prob: float | None
    model_draw_prob: float | None
    model_away_prob: float | None
