# Import all ORM models so SQLAlchemy metadata and relationship string lookups work

from app.infrastructure.persistence_models.dataset import Dataset  # noqa: F401
from app.infrastructure.persistence_models.match import Match  # noqa: F401
from app.infrastructure.persistence_models.odds import Odds  # noqa: F401
from app.infrastructure.persistence_models.simulation_run import (
    SimulationRun,
)  # noqa: F401
from app.infrastructure.persistence_models.user import User  # noqa: F401
