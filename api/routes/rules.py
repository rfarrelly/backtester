from fastapi import APIRouter, HTTPException

from app.domain.simulation.rule_models import RuleValidateRequest, RuleValidateResponse
from app.domain.simulation.rule_validation import validate_rule_expression

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/validate", response_model=RuleValidateResponse)
def validate_rule(req: RuleValidateRequest):
    ok, used, unknown, error = validate_rule_expression(
        expression=req.expression,
        available_names=req.available_names,
        sample_vars=req.sample_vars,
    )

    if not ok:
        # 400 because the user can fix their input
        raise HTTPException(status_code=400, detail=error)

    return RuleValidateResponse(
        ok=True,
        expression=req.expression,
        used_names=used,
        unknown_names=unknown,
        error=None,
    )
