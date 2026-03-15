import { useEffect, useState, type CSSProperties } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { deleteRun, downloadRunBetsCsv, getRun } from "../api/runs";
import type { RunDetail } from "../types/api";
import { saveSimulationDraft } from "../lib/simulationDraft";
import SimulationResultView from "../components/results/SimulationResultView";

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const [run, setRun] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!runId) return;

      setLoading(true);
      setError(null);

      try {
        const data = await getRun(runId);
        setRun(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load run");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [runId]);

  async function handleDelete() {
    if (!runId) return;

    const confirmed = window.confirm("Delete this run?");
    if (!confirmed) return;

    setBusy(true);
    setError(null);

    try {
      await deleteRun(runId);
      navigate("/runs");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete run");
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    if (!runId) return;

    setBusy(true);
    setError(null);

    try {
      await downloadRunBetsCsv(runId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export CSV");
    } finally {
      setBusy(false);
    }
  }

  function handleLoadIntoSimulator() {
    if (!run) return;

    saveSimulationDraft(run.dataset_id, {
      sourceRunId: run.run_id,
      mapping: run.mapping,
      request: {
        ...run.request,
      },
      persist: true,
    });

    navigate(`/datasets/${run.dataset_id}`);
  }

  if (!runId) {
    return <div>Missing run id.</div>;
  }

  if (loading) {
    return <div>Loading run...</div>;
  }

  if (error && !run) {
    return <div style={{ color: "#b00020" }}>{error}</div>;
  }

  if (!run) {
    return <div>No run data available.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 20, minWidth: 0 }}>
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          background: "#fff",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 16,
            flexWrap: "wrap",
            alignItems: "start",
          }}
        >
          <div style={{ display: "grid", gap: 6 }}>
            <h2 style={{ margin: 0 }}>Run detail</h2>
            <div>
              <strong>Run ID:</strong> {run.run_id}
            </div>
            <div>
              <strong>Dataset ID:</strong> {run.dataset_id}
            </div>
            <div>
              <strong>Created:</strong> {run.created_at ?? "-"}
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Link to="/runs">Back to runs</Link>

            <button onClick={handleLoadIntoSimulator} disabled={busy}>
              Load into simulator
            </button>

            <button onClick={handleExport} disabled={busy}>
              {busy ? "Working..." : "Export CSV"}
            </button>

            <button onClick={handleDelete} disabled={busy}>
              {busy ? "Working..." : "Delete run"}
            </button>
          </div>
        </div>
      </section>

      {error && <div style={{ color: "#b00020" }}>{error}</div>}

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          background: "#fff",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Simulation request</h3>
        <div style={summaryGridStyle}>
          <InfoCard label="League" value={run.request.league ?? "-"} />
          <InfoCard
            label="Leagues"
            value={
              run.request.leagues && run.request.leagues.length > 0
                ? run.request.leagues.join(", ")
                : "-"
            }
          />
          <InfoCard label="Season" value={run.request.season} />
          <InfoCard label="Selection" value={run.request.selection ?? "-"} />
          <InfoCard label="Rule" value={run.request.rule_expression ?? "-"} />
          <InfoCard label="Staking" value={run.request.staking_method} />
          <InfoCard
            label="Starting bankroll"
            value={String(run.request.starting_bankroll)}
          />
          <InfoCard label="Multiple legs" value={String(run.request.multiple_legs)} />
          <InfoCard
            label="Min odds"
            value={run.request.min_odds != null ? String(run.request.min_odds) : "-"}
          />
          <InfoCard
            label="Walk-forward"
            value={run.request.walk_forward ? "Yes" : "No"}
          />
          <InfoCard
            label="Period mode"
            value={run.request.period_mode ?? "none"}
          />
          <InfoCard label="Rank by" value={run.request.rank_by ?? "-"} />
          <InfoCard
            label="Max candidates / period"
            value={
              run.request.max_candidates_per_period != null
                ? String(run.request.max_candidates_per_period)
                : "-"
            }
          />
        </div>
      </section>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          background: "#fff",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Dataset mapping</h3>
        <div style={summaryGridStyle}>
          <InfoCard label="Home team col" value={run.mapping.home_team_col} />
          <InfoCard label="Away team col" value={run.mapping.away_team_col} />
          <InfoCard label="Date col" value={run.mapping.date_col} />
          <InfoCard label="Time col" value={run.mapping.time_col ?? "-"} />
          <InfoCard label="League col" value={run.mapping.league_col ?? "-"} />
          <InfoCard label="Season col" value={run.mapping.season_col ?? "-"} />
          <InfoCard label="Result col" value={run.mapping.result_col ?? "-"} />
          <InfoCard
            label="Feature cols"
            value={
              run.mapping.feature_cols && run.mapping.feature_cols.length > 0
                ? run.mapping.feature_cols.join(", ")
                : "-"
            }
          />
        </div>
      </section>

      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          background: "#fff",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Results</h3>
        <SimulationResultView result={run.result} />
      </section>
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
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

const summaryGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
};