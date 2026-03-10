import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteRun, downloadRunBetsCsv, listRuns } from "../api/runs";
import type { RunSummary } from "../types/api";

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyRunId, setBusyRunId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);

    try {
      const data = await listRuns();
      setRuns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load runs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleDelete(runId: string) {
    const confirmed = window.confirm("Delete this run?");
    if (!confirmed) return;

    setBusyRunId(runId);
    setError(null);

    try {
      await deleteRun(runId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete run");
    } finally {
      setBusyRunId(null);
    }
  }

  async function handleExport(runId: string) {
    setBusyRunId(runId);
    setError(null);

    try {
      await downloadRunBetsCsv(runId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export CSV");
    } finally {
      setBusyRunId(null);
    }
  }

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section
        style={{
          border: "1px solid #ddd",
          borderRadius: 10,
          padding: 16,
          background: "#fff",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 8 }}>Saved runs</h2>
        <p style={{ margin: 0, color: "#666" }}>
          Review, reopen, export, and delete persisted simulation runs.
        </p>
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
        {loading ? (
          <div>Loading runs...</div>
        ) : runs.length === 0 ? (
          <div>No saved runs yet.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Created</th>
                  <th style={thStyle}>Run ID</th>
                  <th style={thStyle}>Dataset ID</th>
                  <th style={thStyle}>ROI %</th>
                  <th style={thStyle}>Final bankroll</th>
                  <th style={thStyle}>Total bets</th>
                  <th style={thStyle}>Max DD %</th>
                  <th style={thStyle}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.run_id}>
                    <td style={tdStyle}>{run.created_at ?? "-"}</td>
                    <td style={tdStyle}>{run.run_id}</td>
                    <td style={tdStyle}>{run.dataset_id}</td>
                    <td style={tdStyle}>
                      {run.roi_percent != null ? formatNumber(run.roi_percent) : "-"}
                    </td>
                    <td style={tdStyle}>
                      {run.final_bankroll != null
                        ? formatNumber(run.final_bankroll)
                        : "-"}
                    </td>
                    <td style={tdStyle}>
                      {run.total_bets != null ? run.total_bets : "-"}
                    </td>
                    <td style={tdStyle}>
                      {run.max_drawdown_percent != null
                        ? formatNumber(run.max_drawdown_percent)
                        : "-"}
                    </td>
                    <td style={tdStyle}>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <Link to={`/runs/${run.run_id}`}>Open</Link>

                        <button
                          onClick={() => handleExport(run.run_id)}
                          disabled={busyRunId === run.run_id}
                        >
                          {busyRunId === run.run_id ? "Working..." : "Export CSV"}
                        </button>

                        <button
                          onClick={() => handleDelete(run.run_id)}
                          disabled={busyRunId === run.run_id}
                        >
                          {busyRunId === run.run_id ? "Working..." : "Delete"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
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
  whiteSpace: "nowrap",
  verticalAlign: "top",
};