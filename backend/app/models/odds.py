import uuid

from app.db.base import Base
from sqlalchemy import Column, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Odds(Base):
    __tablename__ = "odds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)

    home_win = Column(Float, nullable=False)
    draw = Column(Float, nullable=False)
    away_win = Column(Float, nullable=False)

    match = relationship("Match", back_populates="odds")
