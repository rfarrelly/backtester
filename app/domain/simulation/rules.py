from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class CompiledRule:
    expr: str
    func: Callable[[dict[str, Any]], bool]
    used_names: set[str]


class RuleCompileError(ValueError):
    pass


_ALLOWED_FUNCS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
}

_ALLOWED_CONSTS = {"True", "False", "None"}


class _RuleValidator(ast.NodeVisitor):
    """
    Validates the AST contains only a safe subset.

    Disallows:
    - attribute access (x.y)
    - subscripts (x[y])
    - comprehensions, lambdas, defs, imports
    - function calls except abs/min/max/round
    """

    def __init__(self):
        self.names: set[str] = set()

    def visit_Name(self, node: ast.Name):
        self.names.add(node.id)

    def visit_Attribute(self, node: ast.Attribute):
        raise RuleCompileError("Attribute access is not allowed (e.g. x.y).")

    def visit_Subscript(self, node: ast.Subscript):
        raise RuleCompileError("Indexing is not allowed (e.g. x['a']).")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCS:
            raise RuleCompileError(
                f"Only these functions are allowed: {sorted(_ALLOWED_FUNCS.keys())}"
            )
        # validate args too
        for a in node.args:
            self.visit(a)
        for kw in node.keywords:
            self.visit(kw.value)

    def generic_visit(self, node):
        # Allowed node types
        allowed = (
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
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.IsNot,
            ast.In,
            ast.NotIn,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
        )
        if not isinstance(node, allowed):
            raise RuleCompileError(
                f"Disallowed expression element: {type(node).__name__}"
            )
        super().generic_visit(node)


def compile_rule(expr: str) -> CompiledRule:
    if not expr or not expr.strip():
        raise RuleCompileError("rule_expression is empty.")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise RuleCompileError(f"Invalid rule syntax: {e.msg} (line {e.lineno})") from e

    v = _RuleValidator()
    v.visit(tree)

    used = {n for n in v.names if n not in _ALLOWED_FUNCS and n not in _ALLOWED_CONSTS}

    code = compile(tree, filename="<rule>", mode="eval")

    def _fn(vars_dict: dict[str, Any]) -> bool:
        # Provide only allowed functions, and variables by name
        env = dict(_ALLOWED_FUNCS)
        env.update(vars_dict)
        # No builtins
        return bool(eval(code, {"__builtins__": {}}, env))

    return CompiledRule(expr=expr, func=_fn, used_names=used)
