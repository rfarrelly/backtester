import type { CSSProperties } from "react";
import type { SweepResultRow } from "../../types/api";
import {
  formatParameterValue,
  formatSweepMetric,
  getParameterValue,
  type SweepSortDirection,
  type SweepSortField,
} from "./sweepAnalytics";

type Props = {
  rows: SweepResultRow[];
  parameterNames: string[];
  sortBy: SweepSortField;
  sortDirection: SweepSortDirection;
  onSortChange: (field: SweepSortField) => void;
};

const metricColumns: Array<{
  key: Exclude<SweepSortField, `parameter:${string}`>;
  label: string;
}> = [
  { key: "roi_percent", label: "ROI %" },
  { key: "total_profit", label: "Profit" },
  { key: "total_bets", label: "Bets" },
  { key: "strike_rate_percent", label: "Strike rate %" },
  { key: "max_drawdown_percent", label: "Max DD %" },
  { key: "profit_factor", label: "Profit factor" },
  { key: "final_bankroll", label: "Final bankroll" },
  { key: "average_odds", label: "Average odds" },
];

export default function SweepResultsTable({
  rows,
  parameterNames,
  sortBy,
  sortDirection,
  onSortChange,
}: Props) {
  if (rows.length === 0) {
    return <div>No sweep rows match the current filters.</div>;
  }

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "100%",
        minWidth: 0,
        overflowX: "auto",
        border: "1px solid #e5e7eb",
        borderRadius: 10,
      }}
    >
      <table
        style={{
          width: "100%",
          maxWidth: "100%",
          borderCollapse: "collapse",
          tableLayout: "fixed",
        }}
      >
        <thead>
          <tr style={{ background: "#f8fafc" }}>
            <th style={thStyle}>Rank</th>
            {parameterNames.map((name) => {
              const field = `parameter:${name}` as const;
              return (
                <SortableHeader
                  key={name}
                  label={name}
                  field={field}
                  sortBy={sortBy}
                  sortDirection={sortDirection}
                  onSortChange={onSortChange}
                />
              );
            })}
            {metricColumns.map((column) => (
              <SortableHeader
                key={column.key}
                label={column.label}
                field={column.key}
                sortBy={sortBy}
                sortDirection={sortDirection}
                onSortChange={onSortChange}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${index}-${JSON.stringify(row.parameters ?? row.params ?? {})}`}>
              <td style={tdStyle}>{index + 1}</td>
              {parameterNames.map((name) => (
                <td key={name} style={tdStyle}>
                  {formatParameterValue(getParameterValue(row, name))}
                </td>
              ))}
              <td style={tdStyle}>{formatSweepMetric(row.roi_percent)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.total_profit)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.total_bets, 0)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.strike_rate_percent)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.max_drawdown_percent)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.profit_factor)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.final_bankroll)}</td>
              <td style={tdStyle}>{formatSweepMetric(row.average_odds)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SortableHeader({
  label,
  field,
  sortBy,
  sortDirection,
  onSortChange,
}: {
  label: string;
  field: SweepSortField;
  sortBy: SweepSortField;
  sortDirection: SweepSortDirection;
  onSortChange: (field: SweepSortField) => void;
}) {
  const active = sortBy === field;
  const arrow = active ? (sortDirection === "asc" ? " ▲" : " ▼") : "";

  return (
    <th style={thStyle}>
      <button
        type="button"
        onClick={() => onSortChange(field)}
        style={{
          border: "none",
          background: "transparent",
          padding: 0,
          font: "inherit",
          cursor: "pointer",
          color: active ? "#0f172a" : "#334155",
          fontWeight: active ? 700 : 600,
          whiteSpace: "normal",
          overflowWrap: "anywhere",
          wordBreak: "break-word",
          textAlign: "left",
        }}
      >
        {label}
        {arrow}
      </button>
    </th>
  );
}

const thStyle: CSSProperties = {
  textAlign: "left",
  borderBottom: "1px solid #e5e7eb",
  padding: "10px 12px",
  whiteSpace: "normal",
  overflowWrap: "anywhere",
  wordBreak: "break-word",
  verticalAlign: "top",
  fontSize: 13,
};

const tdStyle: CSSProperties = {
  borderBottom: "1px solid #f1f5f9",
  padding: "10px 12px",
  verticalAlign: "top",
  fontSize: 14,
  whiteSpace: "normal",
  overflowWrap: "anywhere",
  wordBreak: "break-word",
};
