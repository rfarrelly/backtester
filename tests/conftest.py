import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.infrastructure.db.models  # noqa: F401
from app.infrastructure.db.base import Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
