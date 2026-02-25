from app.models.match import Match
from sqlalchemy.orm import joinedload


class MatchRepository:
    def __init__(self, db):
        self.db = db

    def get_matches(self, league: str, season: int):
        return (
            self.db.query(Match)
            .options(joinedload(Match.odds))
            .filter(Match.league == league)
            .filter(Match.season == season)
            .order_by(Match.kickoff.asc())
            .all()
        )
