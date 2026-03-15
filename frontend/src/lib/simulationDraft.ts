import type {
  CustomPeriodDefinition,
  DatasetMapping,
  SimulationRequest,
} from "../types/api";

export type SimulationDraft = {
  sourceRunId?: string | null;
  mapping: DatasetMapping;
  request: SimulationRequest;
  persist?: boolean;
  savedAt: string;
};

function storageKey(datasetId: string): string {
  return `simDraft:${datasetId}`;
}

function isDayKey(value: unknown): value is CustomPeriodDefinition["start_day"] {
  return (
    value === "mon" ||
    value === "tue" ||
    value === "wed" ||
    value === "thu" ||
    value === "fri" ||
    value === "sat" ||
    value === "sun"
  );
}

function normalizeCustomPeriods(
  value: unknown,
  periodMode: SimulationRequest["period_mode"]
): CustomPeriodDefinition[] | null {
  if (periodMode !== "custom") {
    return null;
  }

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      const record = item as Partial<CustomPeriodDefinition> | null;
      if (!record || typeof record !== "object") return null;
      if (!isDayKey(record.start_day) || !isDayKey(record.end_day)) return null;

      return {
        name: typeof record.name === "string" ? record.name : "",
        start_day: record.start_day,
        end_day: record.end_day,
      } satisfies CustomPeriodDefinition;
    })
    .filter((item): item is CustomPeriodDefinition => item !== null);
}

function normalizeSimulationRequest(
  request: SimulationRequest | Record<string, unknown> | null | undefined
): SimulationRequest {
  const raw = (request ?? {}) as Partial<SimulationRequest>;
  const periodMode: SimulationRequest["period_mode"] =
    raw.period_mode === "custom" ? "custom" : "none";

  return {
    league: raw.league ?? null,
    leagues: Array.isArray(raw.leagues)
      ? raw.leagues.filter((item): item is string => typeof item === "string")
      : [],
    season: typeof raw.season === "string" ? raw.season : "",
    selection: raw.selection ?? null,
    rule_expression:
      typeof raw.rule_expression === "string" && raw.rule_expression.trim().length > 0
        ? raw.rule_expression.trim()
        : null,
    staking_method:
      raw.staking_method === "percent" || raw.staking_method === "kelly"
        ? raw.staking_method
        : "fixed",
    fixed_stake:
      typeof raw.fixed_stake === "number" && Number.isFinite(raw.fixed_stake)
        ? raw.fixed_stake
        : null,
    percent_stake:
      typeof raw.percent_stake === "number" && Number.isFinite(raw.percent_stake)
        ? raw.percent_stake
        : null,
    kelly_fraction:
      typeof raw.kelly_fraction === "number" && Number.isFinite(raw.kelly_fraction)
        ? raw.kelly_fraction
        : null,
    starting_bankroll:
      typeof raw.starting_bankroll === "number" && Number.isFinite(raw.starting_bankroll)
        ? raw.starting_bankroll
        : 1000,
    multiple_legs:
      typeof raw.multiple_legs === "number" && Number.isFinite(raw.multiple_legs)
        ? raw.multiple_legs
        : 1,
    min_odds:
      typeof raw.min_odds === "number" && Number.isFinite(raw.min_odds)
        ? raw.min_odds
        : null,
    walk_forward: Boolean(raw.walk_forward),
    train_window_matches:
      typeof raw.train_window_matches === "number" && Number.isFinite(raw.train_window_matches)
        ? raw.train_window_matches
        : null,
    test_window_matches:
      typeof raw.test_window_matches === "number" && Number.isFinite(raw.test_window_matches)
        ? raw.test_window_matches
        : null,
    step_matches:
      typeof raw.step_matches === "number" && Number.isFinite(raw.step_matches)
        ? raw.step_matches
        : null,
    period_mode: periodMode,
    custom_periods: normalizeCustomPeriods(raw.custom_periods, periodMode),
    reset_bankroll_each_period: Boolean(raw.reset_bankroll_each_period),
    max_candidates_per_period:
      typeof raw.max_candidates_per_period === "number" &&
      Number.isFinite(raw.max_candidates_per_period)
        ? raw.max_candidates_per_period
        : null,
    rank_by: typeof raw.rank_by === "string" && raw.rank_by.length > 0 ? raw.rank_by : null,
    rank_order: raw.rank_order === "desc" ? "desc" : "asc",
    require_full_candidate_count: Boolean(raw.require_full_candidate_count),
  };
}

function normalizeSimulationDraft(
  draft: SimulationDraft | Omit<SimulationDraft, "savedAt">
): SimulationDraft {
  return {
    ...draft,
    sourceRunId: draft.sourceRunId ?? null,
    request: normalizeSimulationRequest(draft.request),
    persist: draft.persist ?? true,
    savedAt:
      "savedAt" in draft && typeof draft.savedAt === "string"
        ? draft.savedAt
        : new Date().toISOString(),
  };
}

export function saveSimulationDraft(
  datasetId: string,
  draft: Omit<SimulationDraft, "savedAt">
): void {
  const payload = normalizeSimulationDraft({
    ...draft,
    savedAt: new Date().toISOString(),
  });

  localStorage.setItem(storageKey(datasetId), JSON.stringify(payload));
}

export function loadSimulationDraft(datasetId: string): SimulationDraft | null {
  const raw = localStorage.getItem(storageKey(datasetId));
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as SimulationDraft;
    return normalizeSimulationDraft(parsed);
  } catch {
    return null;
  }
}

export function clearSimulationDraft(datasetId: string): void {
  localStorage.removeItem(storageKey(datasetId));
}
