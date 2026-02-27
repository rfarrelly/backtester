import { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function formatPct(x) {
  if (x === null || x === undefined) return "-";
  return `${Number(x).toFixed(2)}%`;
}

function formatMoney(x) {
  if (x === null || x === undefined) return "-";
  return Number(x).toFixed(2);
}

function formatDateTime(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

export default function App() {
  const [league, setLeague] = useState("Premier-League");
  const [season, setSeason] = useState("2526");

  const [strategyType, setStrategyType] = useState("home"); // home | edge
  const [selection, setSelection] = useState("H"); // H/D/A
  const [minEdge, setMinEdge] = useState(0.05);

  const [stakingMethod, setStakingMethod] = useState("fixed"); // fixed | percent | kelly
  const [fixedStake, setFixedStake] = useState(100);
  const [percentStake, setPercentStake] = useState(0.02);
  const [kellyFraction, setKellyFraction] = useState(0.5);

  const [multipleLegs, setMultipleLegs] = useState(1);
  const [minOdds, setMinOdds] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [result, setResult] = useState(null);

  const equityData = useMemo(() => {
    if (!result?.equity_curve) return [];
    // equity_curve: [{t: "...", bankroll: number}]  (t can be null for first point)
    return result.equity_curve
      .filter((p) => p && p.bankroll !== undefined && p.bankroll !== null)
      .map((p, idx) => ({
        idx,
        t: p.t ? formatDateTime(p.t) : "Start",
        bankroll: Number(p.bankroll),
      }));
  }, [result]);

  async function runSim(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);
    setResult(null);

    try {
      const payload = {
        league,
        season,
        strategy_type: strategyType,
        selection: strategyType === "edge" ? selection : null,
        min_edge: strategyType === "edge" ? Number(minEdge) : null,

        staking_method: stakingMethod,
        fixed_stake: stakingMethod === "fixed" ? Number(fixedStake) : null,
        percent_stake: stakingMethod === "percent" ? Number(percentStake) : null,
        kelly_fraction: stakingMethod === "kelly" ? Number(kellyFraction) : null,

        starting_bankroll: 1000,
        multiple_legs: Number(multipleLegs),

        min_odds: minOdds === "" ? null : Number(minOdds),
      };

      const res = await fetch(`${API_BASE}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setResult(data);
    } catch (e2) {
      setErr(e2?.message || String(e2));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: "system-ui, Arial", padding: 16, maxWidth: 1200, margin: "0 auto" }}>
      <h2 style={{ margin: "0 0 8px" }}>Backtester MVP</h2>
      <p style={{ marginTop: 0, color: "#555" }}>
        Run a simulation and inspect results (equity curve + bet ledger).
      </p>

      <form onSubmit={runSim} style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, alignItems: "end" }}>
        <div style={{ gridColumn: "span 2" }}>
          <label>League</label>
          <input value={league} onChange={(e) => setLeague(e.target.value)} style={{ width: "100%" }} />
        </div>

        <div style={{ gridColumn: "span 1" }}>
          <label>Season</label>
          <input value={season} onChange={(e) => setSeason(e.target.value)} style={{ width: "100%" }} />
        </div>

        <div style={{ gridColumn: "span 1" }}>
          <label>Strategy</label>
          <select value={strategyType} onChange={(e) => setStrategyType(e.target.value)} style={{ width: "100%" }}>
            <option value="home">Home</option>
            <option value="edge">Edge</option>
          </select>
        </div>

        <div style={{ gridColumn: "span 1" }}>
          <label>Legs</label>
          <input type="number" min="1" value={multipleLegs} onChange={(e) => setMultipleLegs(e.target.value)} style={{ width: "100%" }} />
        </div>

        <div style={{ gridColumn: "span 1" }}>
          <label>Min Odds</label>
          <input value={minOdds} onChange={(e) => setMinOdds(e.target.value)} placeholder="e.g. 1.5" style={{ width: "100%" }} />
        </div>

        {strategyType === "edge" && (
          <>
            <div style={{ gridColumn: "span 1" }}>
              <label>Selection</label>
              <select value={selection} onChange={(e) => setSelection(e.target.value)} style={{ width: "100%" }}>
                <option value="H">H</option>
                <option value="D">D</option>
                <option value="A">A</option>
              </select>
            </div>

            <div style={{ gridColumn: "span 1" }}>
              <label>Min Edge</label>
              <input type="number" step="0.01" value={minEdge} onChange={(e) => setMinEdge(e.target.value)} style={{ width: "100%" }} />
            </div>
          </>
        )}

        <div style={{ gridColumn: "span 1" }}>
          <label>Staking</label>
          <select value={stakingMethod} onChange={(e) => setStakingMethod(e.target.value)} style={{ width: "100%" }}>
            <option value="fixed">Fixed</option>
            <option value="percent">Percent</option>
            <option value="kelly">Kelly</option>
          </select>
        </div>

        {stakingMethod === "fixed" && (
          <div style={{ gridColumn: "span 1" }}>
            <label>Fixed Stake</label>
            <input type="number" value={fixedStake} onChange={(e) => setFixedStake(e.target.value)} style={{ width: "100%" }} />
          </div>
        )}

        {stakingMethod === "percent" && (
          <div style={{ gridColumn: "span 1" }}>
            <label>% Stake (0-1)</label>
            <input type="number" step="0.01" value={percentStake} onChange={(e) => setPercentStake(e.target.value)} style={{ width: "100%" }} />
          </div>
        )}

        {stakingMethod === "kelly" && (
          <div style={{ gridColumn: "span 1" }}>
            <label>Kelly Fraction (0-1)</label>
            <input type="number" step="0.1" value={kellyFraction} onChange={(e) => setKellyFraction(e.target.value)} style={{ width: "100%" }} />
          </div>
        )}

        <div style={{ gridColumn: "span 2" }}>
          <button type="submit" disabled={loading} style={{ width: "100%", padding: "10px 12px" }}>
            {loading ? "Running..." : "Run Simulation"}
          </button>
        </div>
      </form>

      {err && (
        <pre style={{ marginTop: 16, padding: 12, background: "#fee", border: "1px solid #f99", overflowX: "auto" }}>
          {err}
        </pre>
      )}

      {result && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginTop: 16 }}>
            <Card title="Final Bankroll" value={formatMoney(result.final_bankroll)} />
            <Card title="ROI" value={formatPct(result.roi_percent)} />
            <Card title="Bets" value={result.total_bets} />
            <Card title="Wins / Losses" value={`${result.total_wins} / ${result.total_losses}`} />
            <Card title="Max Drawdown" value={formatPct(result.max_drawdown_percent)} />
          </div>

          <h3 style={{ marginTop: 18 }}>Equity Curve</h3>
          <div style={{ height: 260, border: "1px solid #ddd", borderRadius: 8, padding: 8 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="t" hide />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="bankroll" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3 style={{ marginTop: 18 }}>Bets</h3>
          <BetsTable bets={result.bets || []} />
        </>
      )}
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      <div style={{ fontSize: 12, color: "#666" }}>{title}</div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

function BetsTable({ bets }) {
  const [openIdx, setOpenIdx] = useState(null);

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, overflow: "hidden" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead style={{ background: "#f7f7f7" }}>
          <tr>
            <Th>Settled</Th>
            <Th>Stake</Th>
            <Th>Odds</Th>
            <Th>Win</Th>
            <Th>Profit</Th>
            <Th>Legs</Th>
          </tr>
        </thead>
        <tbody>
          {bets.map((b, idx) => (
            <>
              <tr
                key={idx}
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                style={{ cursor: "pointer", borderTop: "1px solid #eee" }}
              >
                <Td>{formatDateTime(b.settled_at)}</Td>
                <Td>{formatMoney(b.stake)}</Td>
                <Td>{Number(b.combined_odds).toFixed(2)}</Td>
                <Td>{b.is_win ? "✅" : "❌"}</Td>
                <Td>{formatMoney(b.profit)}</Td>
                <Td>{(b.legs || b.matches || []).length}</Td>
              </tr>

              {openIdx === idx && (
                <tr style={{ background: "#fcfcfc" }}>
                  <td colSpan={6} style={{ padding: 12 }}>
                    <Legs legs={b.legs || []} selections={b.selections} matches={b.matches} />
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Legs({ legs, selections, matches }) {
  // Support both formats:
  // - new: bet.legs
  // - old: bet.matches + bet.selections
  let normalized = legs;

  if ((!normalized || normalized.length === 0) && matches?.length) {
    normalized = matches.map((m) => {
      const sel = selections?.[m.id];
      return {
        match_id: m.id,
        kickoff: m.kickoff,
        home_team: m.home_team,
        away_team: m.away_team,
        result: m.result,
        selection: sel,
        odds: null,
        implied_prob: null,
        model_prob: null,
        edge: null,
      };
    });
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {normalized.map((l, i) => (
        <div key={i} style={{ border: "1px solid #eee", borderRadius: 8, padding: 10 }}>
          <div style={{ fontWeight: 600 }}>
            {l.home_team} vs {l.away_team} — {formatDateTime(l.kickoff)}
          </div>
          <div style={{ color: "#444", marginTop: 4 }}>
            Selection: <b>{l.selection}</b> &nbsp;|&nbsp; Result: <b>{l.result}</b>
          </div>
          <div style={{ color: "#666", marginTop: 4 }}>
            Odds: <b>{l.odds ?? "-"}</b> &nbsp;|&nbsp; Implied: <b>{l.implied_prob ?? "-"}</b>
            {l.model_prob !== null && l.model_prob !== undefined && (
              <>
                &nbsp;|&nbsp; Model: <b>{l.model_prob}</b> &nbsp;|&nbsp; Edge: <b>{l.edge}</b>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function Th({ children }) {
  return <th style={{ textAlign: "left", padding: "10px 12px", fontSize: 12, color: "#666" }}>{children}</th>;
}
function Td({ children }) {
  return <td style={{ padding: "10px 12px", verticalAlign: "top" }}>{children}</td>;
}