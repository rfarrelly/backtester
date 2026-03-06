from pydantic import BaseModel

from app.application.dataset_mapping import DatasetMapping
from app.domain.simulation.models import SimulationRequest


class DatasetSimulateRequest(BaseModel):
    mapping: DatasetMapping
    request: SimulationRequest
    persist: bool = True
