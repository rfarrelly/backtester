import { apiFetch } from "./client";
import type { RuleValidateRequest, RuleValidateResponse } from "../../src/types/api";

export async function validateRule(
  payload: RuleValidateRequest
): Promise<RuleValidateResponse> {
  return apiFetch<RuleValidateResponse>("/rules/validate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}