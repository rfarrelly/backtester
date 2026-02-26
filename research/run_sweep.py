from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")

from sqlalchemy.orm import Session

from app.application.simulation_service import SimulationService
from app.domain.simulation.models import SimulationRequest
from app.infrastructure.db.session import SessionLocal


def main():
    db: Session = SessionLocal()
    service = SimulationService(db)

    base = SimulationRequest(
        league="Premier-League",
        season="2526",
        strategy_type="home",
        selection="H",
        staking_method="fixed",
        fixed_stake=100,
        starting_bankroll=1000,
        multiple_legs=1,
        min_odds=None,
        min_edge=0.0,  # overridden in sweep
        percent_stake=None,
        kelly_fraction=None,
    )

    for min_edge in [0.00, 0.02, 0.05, 0.08, 0.10]:
        req = base.model_copy(update={"min_edge": min_edge})
        result = service.run(req)
        print(
            f"min_edge={min_edge:.2f}  ROI={result['roi_percent']:.2f}%  "
            f"bets={result['total_bets']}  final={result['final_bankroll']}"
        )


if __name__ == "__main__":
    main()
