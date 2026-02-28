from app.domain.simulation.safe_expr import UnsafeExpressionError, compile_expr


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

        if edge >= self.min_edge:
            return StrategyDecision(True, self.selection)

        return StrategyDecision(False)


class RuleStrategy(BaseStrategy):
    """
    Places a bet when rule_expression evaluates to True.
    Selection is fixed (H/D/A) for MVP.
    """

    def __init__(self, rule_expression: str, selection: str = "H"):
        self.rule_expression = rule_expression
        self.selection = selection

        self._fn = compile_expr(rule_expression)

    def evaluate(self, match, context):
        features = context.features_for_match(match)

        # Add some common aliases
        vars_dict = {
            **features,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "home_goals": match.home_goals,
            "away_goals": match.away_goals,
            "home_win_odds": match.home_win_odds,
            "draw_odds": match.draw_odds,
            "away_win_odds": match.away_win_odds,
        }

        # If any variables are None, eval may fail; treat as "no bet"
        try:
            ok = self._fn(vars_dict)
        except Exception:
            return StrategyDecision(False)

        if ok:
            return StrategyDecision(True, self.selection)

        return StrategyDecision(False)
