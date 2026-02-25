import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    league = Column(String, index=True, nullable=False)
    season = Column(String, index=True, nullable=False)

    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)

    kickoff = Column(DateTime, nullable=False)

    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)

    result = Column(String, nullable=False)  # H, D, A

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    odds = relationship(
        "Odds", back_populates="match", uselist=False, cascade="all, delete-orphan"
    )
