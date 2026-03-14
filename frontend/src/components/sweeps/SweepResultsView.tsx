import { Link } from "react-router-dom";
import type { DatasetSweepResponse } from "../../types/api";

type Props = {
  result: DatasetSweepResponse | null;
};

export default function SweepResultsView({ result }: Props) {
  if (!result) {
    return <div>No sweep run yet.</div>;
  }

  if (result.results.length === 0) {
    return <div>No sweep variants returned.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
        }}
      >
        <SummaryCard label="Total variants" value={String(result.total_variants)} />
        <SummaryCard
          label="Best ROI %"
          value={formatNumber(result.results[0]?.roi_percent ?? 0)}
        />
        <SummaryCard
          label="Best final bankroll"
          value={formatNumber(result.results[0]?.final_bankroll ?? 0)}
        />
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={thStyle}>Rank</th>
              <th style={thStyle}>Params</th>
              <th style={thStyle}>ROI %</th>
              <th style={thStyle}>Final bankroll</th>
              <th style={thStyle}>Bets</th>
              <th style={thStyle}>Max DD %</th>
              <th style={thStyle}>Strike rate %</th>
              <th style={thStyle}>Profit factor</th>
              <th style={thStyle}>Profit</th>
              <th style={thStyle}>Run</th>
            </tr>
          </thead>
          <tbody>
            {result.results.map((row, index) => (
              <tr key={index}>
                <td style={tdStyle}>{index + 1}</td>
                <td style={tdStyle}>
                  <code style={{ whiteSpace: "pre-wrap" }}>
                    {formatParams(row.params)}
                  </code>
                </td>
                <td style={tdStyle}>{formatNumber(row.roi_percent)}</td>
                <td style={tdStyle}>{formatNumber(row.final_bankroll)}</td>
                <td style={tdStyle}>{row.total_bets}</td>
                <td style={tdStyle}>
                  {row.max_drawdown_percent != null
                    ? formatNumber(row.max_drawdown_percent)
                    : "-"}
                </td>
                <td style={tdStyle}>
                  {row.strike_rate_percent != null
                    ? formatNumber(row.strike_rate_percent)
                    : "-"}
                </td>
                <td style={tdStyle}>
                  {row.profit_factor != null ? formatNumber(row.profit_factor) : "-"}
                </td>
                <td style={tdStyle}>
                  {row.total_profit != null ? formatNumber(row.total_profit) : "-"}
                </td>
                <td style={tdStyle}>
                  {row.run_id ? <Link to={`/runs/${row.run_id}`}>Open</Link> : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatParams(params: Record<string, unknown>): string {
  return Object.entries(params)
    .map(([k, v]) => `${k}=${String(v)}`)
    .join(", ");
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        padding: 12,
        background: "#fafafa",
      }}
    >
      <div style={{ fontSize: 12, color: "#666" }}>{label}</div>
      <div style={{ marginTop: 4, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  borderBottom: "1px solid #ddd",
  padding: "8px 12px",
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "8px 12px",
  verticalAlign: "top",
};