import type { SimulationResult } from "../../types/api";

type Props = {
  result: SimulationResult | null;
};

export default function SimulationResultView({ result }: Props) {
  if (!result) {
    return <div>No simulation run yet.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <div style={summaryGridStyle}>
        <SummaryCard label="Run ID" value={result.run_id ?? "-"} />
        <SummaryCard label="Dataset ID" value={result.dataset_id} />
        <SummaryCard label="Final bankroll" value={String(result.final_bankroll)} />
        <SummaryCard label="ROI %" value={String(result.roi_percent)} />
        <SummaryCard label="Total bets" value={String(result.total_bets)} />
        <SummaryCard
          label="Max drawdown %"
          value={result.max_drawdown_percent != null ? String(result.max_drawdown_percent) : "-"}
        />
        <SummaryCard
          label="Strike rate %"
          value={result.strike_rate_percent != null ? String(result.strike_rate_percent) : "-"}
        />
        <SummaryCard
          label="Profit factor"
          value={result.profit_factor != null ? String(result.profit_factor) : "-"}
        />
      </div>

      {result.walk_forward && result.segments && (
        <div>
          <h4 style={{ marginTop: 0 }}>Walk-forward segments</h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Segment</th>
                  <th style={thStyle}>Train start</th>
                  <th style={thStyle}>Train end</th>
                  <th style={thStyle}>Test start</th>
                  <th style={thStyle}>Test end</th>
                  <th style={thStyle}>ROI %</th>
                  <th style={thStyle}>Bets</th>
                </tr>
              </thead>
              <tbody>
                {result.segments.map((segment) => (
                  <tr key={segment.segment_index}>
                    <td style={tdStyle}>{segment.segment_index}</td>
                    <td style={tdStyle}>{segment.train_start_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.train_end_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.test_start_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.test_end_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.roi_percent}</td>
                    <td style={tdStyle}>{segment.total_bets}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div>
        <h4 style={{ marginTop: 0 }}>First bets</h4>
        {result.bets.length === 0 ? (
          <div>No bets placed.</div>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {result.bets.slice(0, 5).map((bet, idx) => (
              <div
                key={idx}
                style={{
                  border: "1px solid #eee",
                  borderRadius: 8,
                  padding: 12,
                  background: "#fafafa",
                }}
              >
                <div>
                  <strong>Stake:</strong> {bet.stake} |{" "}
                  <strong>Combined odds:</strong> {bet.combined_odds} |{" "}
                  <strong>Profit:</strong> {bet.profit}
                </div>

                <div style={{ marginTop: 8, display: "grid", gap: 6 }}>
                  {bet.legs.map((leg, legIdx) => (
                    <div key={legIdx} style={{ fontSize: 14 }}>
                      {leg.kickoff} — {leg.home_team} vs {leg.away_team} —{" "}
                      selection={leg.selection} — result={leg.result}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
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

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: 12,
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  borderBottom: "1px solid #ddd",
  padding: "8px 12px",
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "8px 12px",
  whiteSpace: "nowrap",
};