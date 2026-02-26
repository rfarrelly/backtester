# Import all ORM models so SQLAlchemy relationship string lookups work
from app.infrastructure.persistence_models.match import Match  # noqa: F401
from app.infrastructure.persistence_models.odds import Odds  # noqa: F401
from app.infrastructure.persistence_models.user import User  # noqa: F401
