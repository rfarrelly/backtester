from app.domain.simulation.rules import RuleCompileError, compile_rule


class StrategyDecision:
    def __init__(self, place_bet: bool, selection: str | None = None):
        self.place_bet = place_bet
        self.selection = selection


class BaseStrategy:
    def evaluate(self, match, context=None):
        raise NotImplementedError


# ---------------------------------------------------------
# Deprecated legacy strategies (kept temporarily)
# ---------------------------------------------------------
# These existed before the rule-based system became the
# primary strategy mechanism. They remain only for backward
# compatibility with older runs/tests and will be removed
# in a future cleanup.


class AlwaysHomeStrategy(BaseStrategy):
    """Deprecated: replaced by RuleStrategy(selection='H')."""

    def evaluate(self, match, context=None):
        return StrategyDecision(place_bet=True, selection="H")


class EdgeStrategy(BaseStrategy):
    """Deprecated: replaced by rule expressions."""

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


# ---------------------------------------------------------
# Primary strategy implementation
# ---------------------------------------------------------


class RuleStrategy(BaseStrategy):
    """
    Main strategy used by the simulator.

    Behaviour:

    - If rule_expression is None → all matches eligible
    - If rule_expression exists → only matches where rule evaluates True
    - selection determines which outcome is bet (H/D/A)
    """

    def __init__(self, rule_expression: str | None, selection: str):
        self.rule_expression = rule_expression
        self.selection = selection

        # No rule means "all matches eligible"
        if rule_expression and rule_expression.strip():
            self._compiled = compile_rule(rule_expression)
        else:
            self._compiled = None

    @property
    def used_names(self) -> set[str]:
        if self._compiled is None:
            return set()
        return self._compiled.used_names

    def evaluate(self, match, context=None):
        if self.selection not in ("H", "D", "A"):
            return StrategyDecision(False)

        # No rule expression → allow all matches
        if self._compiled is None:
            return StrategyDecision(True, self.selection)

        vars_dict = {
            "home_team": match.home_team,
            "away_team": match.away_team,
            "home_goals": match.home_goals,
            "away_goals": match.away_goals,
            "home_win_odds": match.home_win_odds,
            "draw_odds": match.draw_odds,
            "away_win_odds": match.away_win_odds,
            "model_home_prob": match.model_home_prob,
            "model_draw_prob": match.model_draw_prob,
            "model_away_prob": match.model_away_prob,
        }

        # Optional rolling context features
        if context is not None and hasattr(context, "features_for_match"):
            vars_dict.update(context.features_for_match(match))

        # Uploaded dataset features
        vars_dict.update(getattr(match, "features", {}) or {})

        try:
            ok = self._compiled.func(vars_dict)
        except (NameError, TypeError):
            return StrategyDecision(False)
        except Exception:
            return StrategyDecision(False)

        if ok:
            return StrategyDecision(True, self.selection)

        return StrategyDecision(False)
