from app.application.strategy_factory import build_strategy
from app.domain.simulation.engine import SimulationEngine


class WalkForwardService:
    def __init__(self):
        pass

    def run(self, matches, request):
        if not request.train_window_matches or not request.test_window_matches:
            raise ValueError(
                "train_window_matches and test_window_matches are required when walk_forward=True"
            )

        step = request.step_matches or request.test_window_matches

        segments = []
        combined_bets = []
        combined_equity_curve = []

        start = 0
        segment_index = 0
        running_bankroll = request.starting_bankroll

        while True:
            train_start = start
            train_end = train_start + request.train_window_matches
            test_end = train_end + request.test_window_matches

            if test_end > len(matches):
                break

            train_matches = matches[train_start:train_end]
            test_matches = matches[train_end:test_end]

            # Use a fresh request per segment so bankroll rolls forward cleanly
            segment_request = request.model_copy(
                update={
                    "starting_bankroll": running_bankroll,
                    "walk_forward": False,
                }
            )

            strategy = build_strategy(segment_request)
            engine = SimulationEngine(segment_request, strategy)
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

            # stitch equity curve
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

        total_profit = running_bankroll - request.starting_bankroll
        aggregate_roi = (
            (total_profit / request.starting_bankroll) * 100
            if request.starting_bankroll
            else 0
        )

        return {
            "walk_forward": True,
            "segments": segments,
            "bets": combined_bets,
            "equity_curve": combined_equity_curve,
            "starting_bankroll": request.starting_bankroll,
            "final_bankroll": round(running_bankroll, 2),
            "roi_percent": round(aggregate_roi, 2),
            "total_segments": len(segments),
            "total_bets": sum(s["total_bets"] for s in segments),
        }
