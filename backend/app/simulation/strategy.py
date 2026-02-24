class StrategyDecision:
    def __init__(self, place_bet: bool, selection: str | None = None):
        self.place_bet = place_bet
        self.selection = selection


class BaseStrategy:
    def evaluate(self, match, context):
        """
        Must return StrategyDecision.
        """
        raise NotImplementedError


class AlwaysHomeStrategy:
    def evaluate(self, match, context):
        return StrategyDecision(place_bet=True, selection="H")


class EdgeStrategy(BaseStrategy):
    def __init__(self, selection: str, min_edge: float = 0.0):
        self.selection = selection
        self.min_edge = min_edge

    def evaluate(self, match, context):
        odds_map = {
            "H": match.odds.home_win,
            "D": match.odds.draw,
            "A": match.odds.away_win,
        }

        prob_map = {
            "H": match.odds.model_home_prob,
            "D": match.odds.model_draw_prob,
            "A": match.odds.model_away_prob,
        }

        odds = odds_map[self.selection]
        model_prob = prob_map[self.selection]

        if model_prob is None:
            return StrategyDecision(False)

        implied_prob = 1 / odds
        edge = model_prob - implied_prob

        if edge > self.min_edge:
            return StrategyDecision(True, self.selection)

        return StrategyDecision(False)
