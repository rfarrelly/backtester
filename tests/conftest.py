import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# IMPORTANT:
# Make sure all ORM models are imported so Base knows about them
import app.infrastructure.persistence_models.dataset  # noqa
import app.infrastructure.persistence_models.match  # noqa
import app.infrastructure.persistence_models.odds  # noqa
import app.infrastructure.persistence_models.user  # noqa
from app.infrastructure.db.base import Base


@pytest.fixture
def db_session():
    # Use SQLite in-memory DB for tests
    engine = create_engine("sqlite:///:memory:")

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
