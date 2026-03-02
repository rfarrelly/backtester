from typing import Any

from pydantic import BaseModel, Field


class RuleValidateRequest(BaseModel):
    expression: str = Field(..., min_length=1)

    # Optional: provide the available variables in the dataset so we can report unknowns.
    available_names: list[str] = []

    # Optional: test the expression on a concrete sample vars dict to catch TypeError etc.
    sample_vars: dict[str, Any] | None = None


class RuleValidateResponse(BaseModel):
    ok: bool
    expression: str
    used_names: list[str]
    unknown_names: list[str]
    error: str | None = None
