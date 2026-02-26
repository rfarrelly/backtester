class StrategyDecision:
    def __init__(self, place_bet: bool, selection: str | None = None):
        self.place_bet = place_bet
        self.selection = selection


class BaseStrategy:
    def evaluate(self, match, context=None):
        raise NotImplementedError


class AlwaysHomeStrategy(BaseStrategy):
    def evaluate(self, match, context=None):
        return StrategyDecision(place_bet=True, selection="H")


class EdgeStrategy(BaseStrategy):
    def __init__(self, selection: str, min_edge: float = 0.0):
        self.selection = selection
        self.min_edge = min_edge

    def evaluate(self, match, context=None):
        if self.selection not in ("H", "D", "A"):
            return StrategyDecision(False)

        odds_map = {
            "H": match.home_win_odds,
            "D": match.draw_odds,
            "A": match.away_win_odds,
        }

        prob_map = {
            "H": match.model_home_prob,
            "D": match.model_draw_prob,
            "A": match.model_away_prob,
        }

        odds = odds_map[self.selection]
        model_prob = prob_map[self.selection]

        if model_prob is None or not odds or odds <= 0:
            return StrategyDecision(False)

        implied_prob = 1 / odds
        edge = model_prob - implied_prob

        if edge > self.min_edge:
            return StrategyDecision(True, self.selection)

        return StrategyDecision(False)
