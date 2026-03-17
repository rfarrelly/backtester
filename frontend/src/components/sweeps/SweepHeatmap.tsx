import type { SweepResultRow } from "../../types/api";
import {
  formatParameterValue,
  formatSweepMetric,
  getParameterValue,
  type SweepMetricField,
} from "./sweepAnalytics";

type Props = {
  rows: SweepResultRow[];
  parameterNames: [string, string];
  metric: Extract<SweepMetricField, "roi_percent" | "total_profit" | "profit_factor">;
};

export default function SweepHeatmap({ rows, parameterNames, metric }: Props) {
  const [xName, yName] = parameterNames;
  const xValues = uniqueValues(rows.map((row) => formatParameterValue(getParameterValue(row, xName))));
  const yValues = uniqueValues(rows.map((row) => formatParameterValue(getParameterValue(row, yName))));
  const metricValues = rows
    .map((row) => row[metric])
    .filter((value): value is number => typeof value === "number" && Number.isFinite(value));

  if (xValues.length === 0 || yValues.length === 0) {
    return null;
  }

  const min = metricValues.length > 0 ? Math.min(...metricValues) : 0;
  const max = metricValues.length > 0 ? Math.max(...metricValues) : 0;

  return (
    <div style={{ display: "grid", gap: 10 }}>
      <div style={{ fontWeight: 700 }}>Heatmap</div>
      <div style={{ fontSize: 13, color: "#475569" }}>
        {metricLabel(metric)} by {xName} and {yName}
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ borderCollapse: "collapse", minWidth: 520 }}>
          <thead>
            <tr>
              <th style={headerCellStyle}>{yName} \ {xName}</th>
              {xValues.map((value) => (
                <th key={value} style={headerCellStyle}>
                  {value}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yValues.map((yValue) => (
              <tr key={yValue}>
                <th style={headerCellStyle}>{yValue}</th>
                {xValues.map((xValue) => {
                  const row = rows.find(
                    (item) =>
                      formatParameterValue(getParameterValue(item, xName)) === xValue &&
                      formatParameterValue(getParameterValue(item, yName)) === yValue
                  );
                  const value = row?.[metric] ?? null;
                  return (
                    <td
                      key={`${yValue}-${xValue}`}
                      style={{
                        ...heatCellStyle,
                        background: getHeatColor(value, min, max),
                      }}
                    >
                      {formatSweepMetric(typeof value === "number" ? value : null)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function uniqueValues(values: string[]): string[] {
  return Array.from(new Set(values)).sort((a, b) =>
    a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  );
}

function getHeatColor(value: number | null | undefined, min: number, max: number): string {
  if (value == null || !Number.isFinite(value)) {
    return "#f8fafc";
  }

  if (max === min) {
    return "rgba(59, 130, 246, 0.18)";
  }

  const normalized = (value - min) / (max - min);
  const alpha = 0.1 + normalized * 0.35;
  return `rgba(59, 130, 246, ${alpha.toFixed(3)})`;
}

function metricLabel(metric: string): string {
  switch (metric) {
    case "roi_percent":
      return "ROI %";
    case "total_profit":
      return "Profit";
    case "profit_factor":
      return "Profit factor";
    default:
      return metric;
  }
}

const headerCellStyle = {
  border: "1px solid #e5e7eb",
  padding: "8px 10px",
  background: "#f8fafc",
  textAlign: "left" as const,
  whiteSpace: "nowrap" as const,
};

const heatCellStyle = {
  border: "1px solid #e5e7eb",
  padding: "10px 12px",
  textAlign: "center" as const,
  minWidth: 92,
  fontWeight: 600,
};
