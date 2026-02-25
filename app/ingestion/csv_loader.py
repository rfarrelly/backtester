import csv
from datetime import datetime

from sqlalchemy.orm import Session

from app.infrastructure.persistence_models.match import Match
from app.infrastructure.persistence_models.odds import Odds


def load_csv(file_path: str, db: Session):
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            kickoff_str = f"{row['Date']} {row['Time']}"
            kickoff = datetime.strptime(kickoff_str, "%Y-%m-%d %H:%M")

            match = Match(
                league=row["League"],
                season=row["Season"],
                home_team=row["HomeTeam"],
                away_team=row["AwayTeam"],
                kickoff=kickoff,
                home_goals=int(row["FTHG"]),
                away_goals=int(row["FTAG"]),
                result=row["FTR"],
            )

            db.add(match)
            db.flush()  # get match.id before commit

            odds = Odds(
                match_id=match.id,
                home_win=float(row["B365CH"]),
                draw=float(row["B365CD"]),
                away_win=float(row["B365CA"]),
            )

            db.add(odds)

        db.commit()
