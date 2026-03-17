import type { SweepResultRow } from "../../types/api";
import {
  formatSweepMetric,
  getBestSweepRows,
} from "./sweepAnalytics";

type Props = {
  rows: SweepResultRow[];
};

export default function SweepSummaryCards({ rows }: Props) {
  const best = getBestSweepRows(rows);

  const cards = [
    {
      label: "Best ROI %",
      value: best.bestRoi ? formatSweepMetric(best.bestRoi.roi_percent) : "-",
      secondary: best.bestRoi ? `${best.bestRoi.total_bets} bets` : undefined,
    },
    {
      label: "Highest profit",
      value: best.bestProfit ? formatSweepMetric(best.bestProfit.total_profit) : "-",
      secondary: best.bestProfit
        ? `ROI ${formatSweepMetric(best.bestProfit.roi_percent)}%`
        : undefined,
    },
    {
      label: "Lowest drawdown",
      value: best.lowestDrawdown
        ? formatSweepMetric(best.lowestDrawdown.max_drawdown_percent)
        : "-",
      secondary: best.lowestDrawdown
        ? `${best.lowestDrawdown.total_bets} bets`
        : undefined,
    },
    {
      label: "Best profit factor",
      value: best.bestProfitFactor
        ? formatSweepMetric(best.bestProfitFactor.profit_factor)
        : "-",
      secondary: best.bestProfitFactor
        ? `Profit ${formatSweepMetric(best.bestProfitFactor.total_profit)}`
        : undefined,
    },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: 12,
      }}
    >
      {cards.map((card) => (
        <div
          key={card.label}
          style={{
            border: "1px solid #e5e7eb",
            borderRadius: 10,
            padding: 14,
            background: "#f8fafc",
          }}
        >
          <div style={{ fontSize: 12, color: "#64748b" }}>{card.label}</div>
          <div style={{ marginTop: 4, fontWeight: 700, fontSize: 20 }}>{card.value}</div>
          {card.secondary ? (
            <div style={{ marginTop: 4, fontSize: 12, color: "#475569" }}>
              {card.secondary}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
