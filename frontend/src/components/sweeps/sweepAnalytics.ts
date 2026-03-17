import type { DatasetSweepResponse, SweepResultRow } from "../../types/api";

export type SweepMetricField =
  | "roi_percent"
  | "total_profit"
  | "total_bets"
  | "strike_rate_percent"
  | "max_drawdown_percent"
  | "profit_factor"
  | "final_bankroll"
  | "average_odds";

export type SweepSortField = SweepMetricField | `parameter:${string}`;
export type SweepSortDirection = "asc" | "desc";

export function getSweepRows(result: DatasetSweepResponse | null): SweepResultRow[] {
  if (!result) return [];
  if (Array.isArray(result.rows)) return result.rows;
  if (Array.isArray(result.results)) return result.results;
  return [];
}

export function getSweepParameterNames(result: DatasetSweepResponse | null): string[] {
  if (!result) return [];
  if (Array.isArray(result.parameter_names) && result.parameter_names.length > 0) {
    return result.parameter_names;
  }

  const first = getSweepRows(result)[0];
  if (!first) return [];
  return Object.keys(first.parameters ?? first.params ?? {});
}

export function filterSweepRowsByMinBets(rows: SweepResultRow[], minBets: number): SweepResultRow[] {
  return rows.filter((row) => (row.total_bets ?? 0) >= minBets);
}

export function sortSweepRows(
  rows: SweepResultRow[],
  sortBy: SweepSortField,
  direction: SweepSortDirection
): SweepResultRow[] {
  const multiplier = direction === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => compareRows(a, b, sortBy) * multiplier);
}

function compareRows(a: SweepResultRow, b: SweepResultRow, sortBy: SweepSortField): number {
  if (sortBy.startsWith("parameter:")) {
    const key = sortBy.slice("parameter:".length);
    const aValue = getParameterValue(a, key);
    const bValue = getParameterValue(b, key);
    return compareUnknown(aValue, bValue);
  }

  const aValue = a[sortBy];
  const bValue = b[sortBy];

  if (aValue == null && bValue == null) return 0;
  if (aValue == null) return 1;
  if (bValue == null) return -1;

  if (typeof aValue === "number" && typeof bValue === "number") {
    if (sortBy === "max_drawdown_percent") {
      return aValue - bValue;
    }
    return aValue - bValue;
  }

  return compareUnknown(aValue, bValue);
}

function compareUnknown(a: unknown, b: unknown): number {
  const aString = String(a ?? "");
  const bString = String(b ?? "");
  return aString.localeCompare(bString, undefined, { numeric: true, sensitivity: "base" });
}

export function getParameterValue(row: SweepResultRow, key: string): unknown {
  return row.parameters?.[key] ?? row.params?.[key] ?? null;
}

export function formatSweepMetric(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "-";
  return Number.isInteger(value) ? String(value) : value.toFixed(digits);
}

export function formatParameterValue(value: unknown): string {
  if (value == null) return "-";
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

export type SweepBestRows = {
  bestRoi: SweepResultRow | null;
  bestProfit: SweepResultRow | null;
  lowestDrawdown: SweepResultRow | null;
  bestProfitFactor: SweepResultRow | null;
};

export function getBestSweepRows(rows: SweepResultRow[]): SweepBestRows {
  return {
    bestRoi: getBestRow(rows, "roi_percent", "desc"),
    bestProfit: getBestRow(rows, "total_profit", "desc"),
    lowestDrawdown: getBestRow(rows, "max_drawdown_percent", "asc"),
    bestProfitFactor: getBestRow(rows, "profit_factor", "desc"),
  };
}

function getBestRow(
  rows: SweepResultRow[],
  field: SweepMetricField,
  direction: SweepSortDirection
): SweepResultRow | null {
  const sorted = sortSweepRows(
    rows.filter((row) => row[field] != null),
    field,
    direction
  );
  return sorted[0] ?? null;
}
