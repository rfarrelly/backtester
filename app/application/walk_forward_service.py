from app.application.strategy_factory import build_strategy
from app.domain.simulation.config import SimulationConfig
from app.domain.simulation.engine import SimulationEngine
from app.domain.simulation.models import SimulationRequest


class WalkForwardService:
    def __init__(self):
        pass

    def run(self, matches, config: SimulationConfig | SimulationRequest):
        if isinstance(config, SimulationRequest):
            config = SimulationConfig.from_request(config)

        if not config.train_window_matches or not config.test_window_matches:
            raise ValueError(
                "train_window_matches and test_window_matches are required when walk_forward=True"
            )

        step = config.step_matches or config.test_window_matches

        segments = []
        combined_bets = []
        combined_equity_curve = []

        start = 0
        segment_index = 0
        running_bankroll = config.starting_bankroll

        while True:
            train_start = start
            train_end = train_start + config.train_window_matches
            test_end = train_end + config.test_window_matches

            if test_end > len(matches):
                break

            train_matches = matches[train_start:train_end]
            test_matches = matches[train_end:test_end]

            segment_config = config.with_starting_bankroll(
                running_bankroll
            ).without_walk_forward()

            strategy = build_strategy(segment_config)
            engine = SimulationEngine(segment_config, strategy)
            result = engine.run(test_matches)

            segment_summary = {
                "segment_index": segment_index,
                "train_start_kickoff": (
                    train_matches[0].kickoff.isoformat() if train_matches else None
                ),
                "train_end_kickoff": (
                    train_matches[-1].kickoff.isoformat() if train_matches else None
                ),
                "test_start_kickoff": (
                    test_matches[0].kickoff.isoformat() if test_matches else None
                ),
                "test_end_kickoff": (
                    test_matches[-1].kickoff.isoformat() if test_matches else None
                ),
                "starting_bankroll": running_bankroll,
                "final_bankroll": result["final_bankroll"],
                "roi_percent": result["roi_percent"],
                "total_bets": result["total_bets"],
                "total_wins": result["total_wins"],
                "total_losses": result["total_losses"],
                "strike_rate_percent": result["strike_rate_percent"],
                "max_drawdown_percent": result["max_drawdown_percent"],
                "profit_factor": result.get("profit_factor"),
            }

            segments.append(segment_summary)
            combined_bets.extend(result["bets"])

            for point in result.get("equity_curve", []):
                combined_equity_curve.append(
                    {
                        **point,
                        "segment_index": segment_index,
                    }
                )

            running_bankroll = result["final_bankroll"]
            segment_index += 1
            start += step

        total_profit = running_bankroll - config.starting_bankroll
        aggregate_roi = (
            (total_profit / config.starting_bankroll) * 100
            if config.starting_bankroll
            else 0
        )

        return {
            "walk_forward": True,
            "segments": segments,
            "bets": combined_bets,
            "equity_curve": combined_equity_curve,
            "starting_bankroll": config.starting_bankroll,
            "final_bankroll": round(running_bankroll, 2),
            "roi_percent": round(aggregate_roi, 2),
            "total_segments": len(segments),
            "total_bets": sum(s["total_bets"] for s in segments),
        }
