import ast
import math


class UnsafeExpressionError(ValueError):
    pass


_ALLOWED_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
}


_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
)


def compile_expr(expr: str):
    """
    Compile a safe boolean expression into a callable(vars_dict) -> bool.
    Only supports a restricted subset of Python AST.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise UnsafeExpressionError(f"Invalid expression syntax: {e}") from e

    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise UnsafeExpressionError(f"Disallowed syntax: {type(node).__name__}")

        # no attribute access like a.b
        if isinstance(node, ast.Attribute):
            raise UnsafeExpressionError("Attribute access is not allowed")

        # no subscripting like x[0]
        if isinstance(node, ast.Subscript):
            raise UnsafeExpressionError("Subscript access is not allowed")

        # calls only to whitelisted functions
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise UnsafeExpressionError("Only simple function calls allowed")
            if node.func.id not in _ALLOWED_FUNCS:
                raise UnsafeExpressionError(f"Function '{node.func.id}' is not allowed")

    code = compile(tree, filename="<rule>", mode="eval")

    def _eval(vars_dict: dict) -> bool:
        safe_globals = {"__builtins__": {}}
        safe_globals.update(_ALLOWED_FUNCS)
        return bool(eval(code, safe_globals, vars_dict))

    return _eval
