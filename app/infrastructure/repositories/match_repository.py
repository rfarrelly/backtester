from sqlalchemy.orm import Session

from app.domain.simulation.entities import Match
from app.infrastructure.persistence_models.match import Match as ORMMatch


class MatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_matches(
        self,
        *,
        season: str,
        league: str | None = None,
        leagues: list[str] | None = None,
    ) -> list[Match]:
        query = (
            self.db.query(ORMMatch)
            .filter(ORMMatch.season == season)
            .order_by(ORMMatch.kickoff.asc())
        )

        if leagues:
            normalized_leagues = [
                value.strip() for value in leagues if value and value.strip()
            ]
            if normalized_leagues:
                query = query.filter(ORMMatch.league.in_(normalized_leagues))
        elif league:
            query = query.filter(ORMMatch.league == league.strip())

        orm_matches = query.all()
        return [self._to_domain(m) for m in orm_matches]

    def _to_domain(self, orm: ORMMatch) -> Match:
        odds = orm.odds

        return Match(
            id=orm.id,
            league=orm.league,
            season=orm.season,
            kickoff=orm.kickoff,
            home_team=orm.home_team,
            away_team=orm.away_team,
            home_goals=orm.home_goals,
            away_goals=orm.away_goals,
            result=orm.result,
            home_win_odds=odds.home_win,
            draw_odds=odds.draw,
            away_win_odds=odds.away_win,
            model_home_prob=odds.model_home_prob,
            model_draw_prob=odds.model_draw_prob,
            model_away_prob=odds.model_away_prob,
        )
