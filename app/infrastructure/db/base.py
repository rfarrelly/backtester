from sqlalchemy.orm import DeclarativeBase

# IMPORTANT: import models so they're registered with SQLAlchemy
import app.infrastructure.persistence_models  # noqa: F401


class Base(DeclarativeBase):
    pass
