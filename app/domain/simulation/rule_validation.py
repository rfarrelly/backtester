from typing import Any

from app.domain.simulation.rules import RuleCompileError, compile_rule


def validate_rule_expression(
    expression: str,
    available_names: list[str] | None = None,
    sample_vars: dict[str, Any] | None = None,
):
    """
    Returns (ok, used_names, unknown_names, error_message)
    """
    available_set = set(available_names or [])

    try:
        compiled = compile_rule(expression)
    except RuleCompileError as e:
        return False, [], [], str(e)

    used = sorted(compiled.used_names)
    unknown = sorted(
        [n for n in compiled.used_names if available_set and n not in available_set]
    )

    # Optional runtime check (helps users catch None comparisons etc.)
    if sample_vars is not None:
        try:
            compiled.func(sample_vars)
        except Exception as e:
            # keep message short and useful
            return (
                False,
                used,
                unknown,
                f"Rule evaluated with error on sample_vars: {type(e).__name__}: {e}",
            )

    return True, used, unknown, None
