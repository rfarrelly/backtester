import csv
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from app.application.dataset_mapping import DatasetMapping
from app.domain.simulation.entities import Match


def _parse_float(x: Any) -> float | None:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in {"na", "nan", "null", "none"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_int(x: Any) -> int | None:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in {"na", "nan", "null", "none"}:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


from datetime import datetime


def _parse_kickoff(row: dict[str, str], mapping: DatasetMapping) -> datetime:
    if not mapping.result_col:
        raise ValueError(
            "result_col is required for backtesting (needed to settle bets)"
        )

    date_str = (row.get(mapping.date_col) or "").strip()
    if not date_str:
        raise ValueError(f"Missing date value in column '{mapping.date_col}'")

    time_str = "00:00"
    if mapping.time_col:
        # If mapping specifies a time column but this file doesn't have it, default safely
        time_str = (row.get(mapping.time_col) or "").strip() or "00:00"

    # If formats provided, use them
    if mapping.date_format and mapping.time_format:
        return datetime.strptime(
            f"{date_str} {time_str}", f"{mapping.date_format} {mapping.time_format}"
        )

    # Sensible default: ISO date + HH:MM
    # Try date+time first
    try:
        return datetime.fromisoformat(f"{date_str} {time_str}")
    except ValueError:
        # Try date only
        return datetime.fromisoformat(date_str)


def load_matches_from_csv(
    csv_path: str | Path,
    mapping: DatasetMapping,
    default_league: str = "Unknown",
    default_season: str = "Unknown",
) -> list[Match]:
    csv_path = Path(csv_path)

    matches: list[Match] = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            kickoff = _parse_kickoff(row, mapping)

            league = (
                row[mapping.league_col].strip()
                if mapping.league_col
                else default_league
            )
            season = (
                row[mapping.season_col].strip()
                if mapping.season_col
                else default_season
            )

            home_team = row[mapping.home_team_col].strip()
            away_team = row[mapping.away_team_col].strip()

            # result/goals optional (but engine needs result for settlement)
            result = row[mapping.result_col].strip() if mapping.result_col else "H"
            home_goals = (
                _parse_int(row.get(mapping.home_goals_col))
                if mapping.home_goals_col
                else 0
            )
            away_goals = (
                _parse_int(row.get(mapping.away_goals_col))
                if mapping.away_goals_col
                else 0
            )

            # odds optional; if missing we set harmless defaults
            home_odds = (
                _parse_float(row.get(mapping.odds_home_col))
                if mapping.odds_home_col
                else 2.0
            )
            draw_odds = (
                _parse_float(row.get(mapping.odds_draw_col))
                if mapping.odds_draw_col
                else 3.5
            )
            away_odds = (
                _parse_float(row.get(mapping.odds_away_col))
                if mapping.odds_away_col
                else 4.0
            )

            # model probs optional
            mhp = (
                _parse_float(row.get(mapping.model_home_prob_col))
                if mapping.model_home_prob_col
                else None
            )
            mdp = (
                _parse_float(row.get(mapping.model_draw_prob_col))
                if mapping.model_draw_prob_col
                else None
            )
            map_ = (
                _parse_float(row.get(mapping.model_away_prob_col))
                if mapping.model_away_prob_col
                else None
            )

            # features
            features: dict[str, Any] = {}
            for col in mapping.feature_cols:
                if col in row:
                    v = _parse_float(row[col])
                    # keep numeric only for MVP; later we can preserve strings too
                    features[col] = v

            matches.append(
                Match(
                    id=uuid.uuid4(),
                    league=league,
                    season=season,
                    kickoff=kickoff,
                    home_team=home_team,
                    away_team=away_team,
                    home_goals=home_goals or 0,
                    away_goals=away_goals or 0,
                    result=result,
                    home_win_odds=home_odds or 2.0,
                    draw_odds=draw_odds or 3.5,
                    away_win_odds=away_odds or 4.0,
                    model_home_prob=mhp,
                    model_draw_prob=mdp,
                    model_away_prob=map_,
                    features=features,
                )
            )

    # Ensure chronological order for engine
    matches.sort(key=lambda m: m.kickoff)
    return matches
