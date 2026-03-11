import React, { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { SimulationResult } from "../../types/api";

type Props = {
  result: SimulationResult | null;
};

type EquityChartPoint = {
  index: number;
  bankroll: number;
  label: string;
};

export default function SimulationResultView({ result }: Props) {
  const [expandedBetIndex, setExpandedBetIndex] = useState<number | null>(null);

  const equityData = useMemo<EquityChartPoint[]>(() => {
    if (!result?.equity_curve || result.equity_curve.length === 0) {
      return [];
    }

    return result.equity_curve.map((point, index) => ({
      index,
      bankroll: point.bankroll,
      label:
        point.t ??
        (point.period_label
          ? `${point.period_label} #${(point.period_index ?? 0) + 1}`
          : point.segment_index != null
          ? `Segment ${point.segment_index + 1}`
          : `Point ${index + 1}`),
    }));
  }, [result]);

  if (!result) {
    return <div>No simulation run yet.</div>;
  }

  const isCalendarMode = Boolean((result as any).calendar_periods);
  const calendarPeriods = (result as any).periods ?? [];

  return (
    <div style={{ display: "grid", gap: 24, minWidth: 0 }}>
      <section>
        <h4 style={{ marginTop: 0 }}>Summary</h4>
        <div style={summaryGridStyle}>
          <SummaryCard label="Run ID" value={result.run_id ?? "-"} />
          <SummaryCard label="Dataset ID" value={result.dataset_id} />
          <SummaryCard label="Final bankroll" value={formatNumber(result.final_bankroll)} />
          <SummaryCard label="ROI %" value={formatNumber(result.roi_percent)} />
          <SummaryCard label="Total bets" value={String(result.total_bets)} />
          <SummaryCard
            label="Max drawdown %"
            value={
              result.max_drawdown_percent != null
                ? formatNumber(result.max_drawdown_percent)
                : "-"
            }
          />
          <SummaryCard
            label="Strike rate %"
            value={
              result.strike_rate_percent != null
                ? formatNumber(result.strike_rate_percent)
                : "-"
            }
          />
          <SummaryCard
            label="Profit factor"
            value={result.profit_factor != null ? formatNumber(result.profit_factor) : "-"}
          />
          {isCalendarMode && (
            <SummaryCard
              label="Total periods"
              value={String((result as any).total_periods ?? calendarPeriods.length)}
            />
          )}
          {result.walk_forward && (
            <SummaryCard
              label="Total segments"
              value={String(result.total_segments ?? result.segments?.length ?? 0)}
            />
          )}
        </div>
      </section>

      <section>
        <h4 style={{ marginTop: 0 }}>Equity curve</h4>
        {equityData.length === 0 ? (
          <div>No equity curve available.</div>
        ) : (
          <div
            style={{
              width: "100%",
              maxWidth: "100%",
              minWidth: 0,
              height: 320,
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: 12,
              background: "#fff",
              boxSizing: "border-box",
              overflow: "hidden",
            }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="index"
                  tickFormatter={(value) => String(Number(value) + 1)}
                />
                <YAxis domain={["auto", "auto"]} />
                <Tooltip
                  formatter={(value) => [value ?? "-", "Bankroll"]}
                  labelFormatter={(label) => {
                    if (typeof label !== "number") {
                      return String(label ?? "");
                    }
                    const point = equityData[label];
                    return point ? point.label : `Point ${label + 1}`;
                  }}
                />
                <Line type="monotone" dataKey="bankroll" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      {result.walk_forward && result.segments && (
        <section>
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
                  <th style={thStyle}>Final bankroll</th>
                </tr>
              </thead>
              <tbody>
                {result.segments.map((segment) => (
                  <tr key={segment.segment_index}>
                    <td style={tdStyle}>{segment.segment_index + 1}</td>
                    <td style={tdStyle}>{segment.train_start_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.train_end_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.test_start_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{segment.test_end_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{formatNumber(segment.roi_percent)}</td>
                    <td style={tdStyle}>{segment.total_bets}</td>
                    <td style={tdStyle}>{formatNumber(segment.final_bankroll)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {isCalendarMode && calendarPeriods.length > 0 && (
        <section>
          <h4 style={{ marginTop: 0 }}>Calendar periods</h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Period</th>
                  <th style={thStyle}>Label</th>
                  <th style={thStyle}>Start</th>
                  <th style={thStyle}>End</th>
                  <th style={thStyle}>Start bankroll</th>
                  <th style={thStyle}>Final bankroll</th>
                  <th style={thStyle}>ROI %</th>
                  <th style={thStyle}>Bets</th>
                  <th style={thStyle}>Strike rate %</th>
                  <th style={thStyle}>Max DD %</th>
                  <th style={thStyle}>Profit factor</th>
                </tr>
              </thead>
              <tbody>
                {calendarPeriods.map((period: any) => (
                  <tr key={period.period_index}>
                    <td style={tdStyle}>{Number(period.period_index) + 1}</td>
                    <td style={tdStyle}>{period.period_label ?? "-"}</td>
                    <td style={tdStyle}>{period.start_kickoff ?? "-"}</td>
                    <td style={tdStyle}>{period.end_kickoff ?? "-"}</td>
                    <td style={tdStyle}>
                      {period.starting_bankroll != null
                        ? formatNumber(period.starting_bankroll)
                        : "-"}
                    </td>
                    <td style={tdStyle}>
                      {period.final_bankroll != null
                        ? formatNumber(period.final_bankroll)
                        : "-"}
                    </td>
                    <td style={tdStyle}>
                      {period.roi_percent != null ? formatNumber(period.roi_percent) : "-"}
                    </td>
                    <td style={tdStyle}>
                      {period.total_bets != null ? String(period.total_bets) : "-"}
                    </td>
                    <td style={tdStyle}>
                      {period.strike_rate_percent != null
                        ? formatNumber(period.strike_rate_percent)
                        : "-"}
                    </td>
                    <td style={tdStyle}>
                      {period.max_drawdown_percent != null
                        ? formatNumber(period.max_drawdown_percent)
                        : "-"}
                    </td>
                    <td style={tdStyle}>
                      {period.profit_factor != null
                        ? formatNumber(period.profit_factor)
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section>
        <h4 style={{ marginTop: 0 }}>Bets</h4>

        {result.bets.length === 0 ? (
          <div>No bets placed.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>#</th>
                  <th style={thStyle}>Settled at</th>
                  <th style={thStyle}>Stake</th>
                  <th style={thStyle}>Combined odds</th>
                  <th style={thStyle}>Win</th>
                  <th style={thStyle}>Profit</th>
                  <th style={thStyle}>Return</th>
                  <th style={thStyle}>Legs</th>
                  <th style={thStyle}>Details</th>
                </tr>
              </thead>
              <tbody>
                {result.bets.map((bet, index) => {
                  const expanded = expandedBetIndex === index;

                  return (
                    <React.Fragment key={`bet-group-${index}`}>
                      <tr>
                        <td style={tdStyle}>{index + 1}</td>
                        <td style={tdStyle}>{bet.settled_at ?? "-"}</td>
                        <td style={tdStyle}>{formatNumber(bet.stake)}</td>
                        <td style={tdStyle}>{formatNumber(bet.combined_odds)}</td>
                        <td style={tdStyle}>{bet.is_win ? "Yes" : "No"}</td>
                        <td style={tdStyle}>{formatNumber(bet.profit)}</td>
                        <td style={tdStyle}>{formatNumber(bet.return_amount)}</td>
                        <td style={tdStyle}>{bet.legs.length}</td>
                        <td style={tdStyle}>
                          <button
                            onClick={() =>
                              setExpandedBetIndex(expanded ? null : index)
                            }
                          >
                            {expanded ? "Hide" : "Show"}
                          </button>
                        </td>
                      </tr>

                      {expanded && (
                        <tr>
                          <td style={expandedTdStyle} colSpan={9}>
                            <div style={{ display: "grid", gap: 12 }}>
                              {bet.legs.map((leg, legIndex) => (
                                <div
                                  key={legIndex}
                                  style={{
                                    border: "1px solid #ddd",
                                    borderRadius: 8,
                                    padding: 12,
                                    background: "#fafafa",
                                  }}
                                >
                                  <div style={{ marginBottom: 8 }}>
                                    <strong>Leg {legIndex + 1}</strong>
                                  </div>

                                  <div style={{ display: "grid", gap: 4 }}>
                                    <div>
                                      <strong>Kickoff:</strong> {leg.kickoff}
                                    </div>
                                    <div>
                                      <strong>Fixture:</strong> {leg.home_team} vs{" "}
                                      {leg.away_team}
                                    </div>
                                    <div>
                                      <strong>Selection:</strong> {leg.selection}
                                    </div>
                                    <div>
                                      <strong>Result:</strong> {leg.result}
                                    </div>
                                    <div>
                                      <strong>Odds:</strong>{" "}
                                      {leg.odds != null ? formatNumber(leg.odds) : "-"}
                                    </div>
                                    <div>
                                      <strong>Implied prob:</strong>{" "}
                                      {leg.implied_prob != null
                                        ? formatNumber(leg.implied_prob)
                                        : "-"}
                                    </div>
                                    <div>
                                      <strong>Model prob:</strong>{" "}
                                      {leg.model_prob != null
                                        ? formatNumber(leg.model_prob)
                                        : "-"}
                                    </div>
                                    <div>
                                      <strong>Edge:</strong>{" "}
                                      {leg.edge != null ? formatNumber(leg.edge) : "-"}
                                    </div>
                                  </div>

                                  {leg.features &&
                                    Object.keys(leg.features).length > 0 && (
                                      <div style={{ marginTop: 12 }}>
                                        <strong>Features</strong>
                                        <div
                                          style={{
                                            marginTop: 8,
                                            display: "grid",
                                            gridTemplateColumns:
                                              "repeat(auto-fit, minmax(180px, 1fr))",
                                            gap: 8,
                                          }}
                                        >
                                          {Object.entries(leg.features).map(
                                            ([key, value]) => (
                                              <div
                                                key={key}
                                                style={{
                                                  border: "1px solid #eee",
                                                  borderRadius: 6,
                                                  padding: 8,
                                                  background: "#fff",
                                                }}
                                              >
                                                <div
                                                  style={{
                                                    fontSize: 12,
                                                    color: "#666",
                                                  }}
                                                >
                                                  {key}
                                                </div>
                                                <div>{String(value)}</div>
                                              </div>
                                            )
                                          )}
                                        </div>
                                      </div>
                                    )}
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
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
      <div style={{ marginTop: 4, fontWeight: 600, wordBreak: "break-word" }}>
        {value}
      </div>
    </div>
  );
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
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
  verticalAlign: "top",
};

const expandedTdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "12px",
  background: "#fcfcfc",
};