from pydantic import BaseModel


class DatasetMapping(BaseModel):
    # required identification/time
    home_team_col: str
    away_team_col: str
    date_col: str
    time_col: str | None = None

    # date/time parsing
    date_format: str | None = None  # e.g. "%Y-%m-%d"
    time_format: str | None = None  # e.g. "%H:%M"

    # optional fields
    league_col: str | None = None
    season_col: str | None = None

    result_col: str | None = None
    home_goals_col: str | None = None
    away_goals_col: str | None = None

    # odds columns (optional)
    odds_home_col: str | None = None
    odds_draw_col: str | None = None
    odds_away_col: str | None = None

    # model probs (optional)
    model_home_prob_col: str | None = None
    model_draw_prob_col: str | None = None
    model_away_prob_col: str | None = None

    # which columns should be treated as features
    feature_cols: list[str] = []
