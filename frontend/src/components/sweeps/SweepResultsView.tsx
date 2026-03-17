import { useMemo, useState } from "react";
import type { DatasetSweepResponse } from "../../types/api";
import SweepHeatmap from "./SweepHeatmap";
import SweepResultsTable from "./SweepResultsTable";
import SweepSummaryCards from "./SweepSummaryCards";
import {
  filterSweepRowsByMinBets,
  formatSweepMetric,
  getSweepParameterNames,
  getSweepRows,
  sortSweepRows,
  type SweepMetricField,
  type SweepSortDirection,
  type SweepSortField,
} from "./sweepAnalytics";

type Props = {
  result: DatasetSweepResponse | null;
};

export default function SweepResultsView({ result }: Props) {
  const rows = useMemo(() => getSweepRows(result), [result]);
  const parameterNames = useMemo(() => getSweepParameterNames(result), [result]);

  const [minBets, setMinBets] = useState(0);
  const [sortBy, setSortBy] = useState<SweepSortField>("roi_percent");
  const [sortDirection, setSortDirection] = useState<SweepSortDirection>("desc");
  const [heatmapMetric, setHeatmapMetric] = useState<Extract<SweepMetricField, "roi_percent" | "total_profit" | "profit_factor">>("roi_percent");

  const filteredRows = useMemo(() => filterSweepRowsByMinBets(rows, minBets), [rows, minBets]);
  const sortedRows = useMemo(
    () => sortSweepRows(filteredRows, sortBy, sortDirection),
    [filteredRows, sortBy, sortDirection]
  );

  if (!result) {
    return <div>No sweep run yet.</div>;
  }

  if (rows.length === 0) {
    return <div>No sweep variants returned.</div>;
  }

  function handleSortChange(field: SweepSortField) {
    if (field === sortBy) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
      return;
    }
    setSortBy(field);
    setSortDirection(field === "max_drawdown_percent" ? "asc" : "desc");
  }

  const totalVariants = result.row_count ?? result.total_variants ?? rows.length;
  const showHeatmap = parameterNames.length === 2 && sortedRows.length > 0;

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div style={{ fontSize: 12, color: "#64748b" }}>Sweep results</div>
          <div style={{ marginTop: 4, fontSize: 20, fontWeight: 700 }}>
            {totalVariants} variants
          </div>
          <div style={{ marginTop: 4, fontSize: 13, color: "#475569" }}>
            Showing {sortedRows.length} after filtering by minimum bet count.
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <label style={{ display: "grid", gap: 4 }}>
            <span style={{ fontSize: 13, color: "#475569" }}>Minimum bets</span>
            <input
              type="number"
              min={0}
              value={minBets}
              onChange={(e) => setMinBets(Math.max(0, Number(e.target.value) || 0))}
              style={{ padding: 8, minWidth: 120 }}
            />
          </label>

          {showHeatmap ? (
            <label style={{ display: "grid", gap: 4 }}>
              <span style={{ fontSize: 13, color: "#475569" }}>Heatmap metric</span>
              <select
                value={heatmapMetric}
                onChange={(e) =>
                  setHeatmapMetric(
                    e.target.value as Extract<
                      SweepMetricField,
                      "roi_percent" | "total_profit" | "profit_factor"
                    >
                  )
                }
                style={{ padding: 8, minWidth: 160 }}
              >
                <option value="roi_percent">ROI %</option>
                <option value="total_profit">Profit</option>
                <option value="profit_factor">Profit factor</option>
              </select>
            </label>
          ) : null}
        </div>
      </div>

      <SweepSummaryCards rows={sortedRows} />

      <div
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: 10,
          background: "#fff",
          padding: 12,
          display: "flex",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <InfoPill label="Parameters" value={parameterNames.join(", ") || "-"} />
        <InfoPill label="Best ROI %" value={formatSweepMetric(sortedRows[0]?.roi_percent)} />
        <InfoPill label="Best profit" value={formatSweepMetric(sortSweepRows(filteredRows, "total_profit", "desc")[0]?.total_profit)} />
      </div>

      {showHeatmap ? (
        <SweepHeatmap
          rows={sortedRows}
          parameterNames={parameterNames as [string, string]}
          metric={heatmapMetric}
        />
      ) : null}

      <SweepResultsTable
        rows={sortedRows}
        parameterNames={parameterNames}
        sortBy={sortBy}
        sortDirection={sortDirection}
        onSortChange={handleSortChange}
      />
    </div>
  );
}

function InfoPill({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        borderRadius: 999,
        border: "1px solid #e5e7eb",
        background: "#f8fafc",
        padding: "8px 12px",
      }}
    >
      <span style={{ fontSize: 12, color: "#64748b" }}>{label}: </span>
      <span style={{ fontSize: 13, fontWeight: 600 }}>{value}</span>
    </div>
  );
}
