from sqlalchemy.orm import Session

from app.infrastructure.persistence_models.simulation_run import SimulationRun


class SimulationRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, run: SimulationRun) -> SimulationRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_for_user(self, owner_user_id):
        return (
            self.db.query(SimulationRun)
            .filter(SimulationRun.owner_user_id == owner_user_id)
            .order_by(SimulationRun.created_at.desc())
            .all()
        )

    def get_for_user(self, run_id, owner_user_id):
        return (
            self.db.query(SimulationRun)
            .filter(SimulationRun.id == run_id)
            .filter(SimulationRun.owner_user_id == owner_user_id)
            .first()
        )

    def delete(self, run: SimulationRun):
        self.db.delete(run)
        self.db.commit()
