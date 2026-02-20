from typing import Literal

from pydantic import BaseModel


class SimpleBacktestRequest(BaseModel):
    league: str
    season: str
    selection: Literal["H", "D", "A"]
    min_odds: float | None = None
    stake: float
