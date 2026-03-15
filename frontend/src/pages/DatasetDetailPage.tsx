import { useEffect, useMemo, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { useParams } from "react-router-dom";
import {
  getDistinctValues,
  introspectDataset,
  simulateDataset,
} from "../api/datasets";
import { runDatasetSweep } from "../api/sweeps";
import {
  clearSimulationDraft,
  loadSimulationDraft,
  saveSimulationDraft,
} from "../lib/simulationDraft";
import type {
  DatasetIntrospection,
  DatasetMapping,
  DatasetSweepResponse,
  SimulationRequest,
  SimulationResult,
} from "../types/api";
import MappingForm from "../components/mapping/MappingForm";
import RuleEditor from "../components/rules/RuleEditor";
import SimulationForm from "../components/simulation/SimulationForm";
import SimulationResultView from "../components/results/SimulationResultView";
import SweepForm from "../components/sweeps/SweepForm";
import SweepResultsView from "../components/sweeps/SweepResultsView";

function buildInitialMapping(): DatasetMapping {
  return {
    home_team_col: "",
    away_team_col: "",
    date_col: "",
    time_col: null,
    date_format: null,
    time_format: null,
    league_col: null,
    season_col: null,
    result_col: null,
    home_goals_col: null,
    away_goals_col: null,
    odds_home_col: null,
    odds_draw_col: null,
    odds_away_col: null,
    model_home_prob_col: null,
    model_draw_prob_col: null,
    model_away_prob_col: null,
    feature_cols: [],
  };
}

function buildInitialSimulationRequest(): SimulationRequest {
  return {
    league: null,
    leagues: [],
    season: "",
    selection: null,
    rule_expression: null,
    staking_method: "fixed",
    fixed_stake: 100,
    percent_stake: null,
    kelly_fraction: null,
    starting_bankroll: 1000,
    multiple_legs: 1,
    min_odds: null,
    walk_forward: false,
    train_window_matches: null,
    test_window_matches: null,
    step_matches: null,
    period_mode: "none",
    custom_periods: null,
    reset_bankroll_each_period: false,
    max_candidates_per_period: null,
    rank_by: null,
    rank_order: "asc",
    require_full_candidate_count: false,
  };
}

function normalizeRequest(request: SimulationRequest): SimulationRequest {
  const normalized: SimulationRequest = {
    ...request,
    league: request.league ?? null,
    leagues: request.leagues ?? [],
    rule_expression:
      request.rule_expression && request.rule_expression.trim().length > 0
        ? request.rule_expression.trim()
        : null,
    min_odds: request.min_odds ?? null,
    train_window_matches: request.train_window_matches ?? null,
    test_window_matches: request.test_window_matches ?? null,
    step_matches: request.step_matches ?? null,
    max_candidates_per_period: request.max_candidates_per_period ?? null,
    rank_by: request.rank_by ?? null,
    custom_periods:
      request.period_mode === "custom" ? request.custom_periods ?? [] : null,
  };

  if (request.staking_method === "fixed") {
    normalized.fixed_stake = request.fixed_stake ?? null;
    normalized.percent_stake = null;
    normalized.kelly_fraction = null;
  } else if (request.staking_method === "percent") {
    normalized.fixed_stake = null;
    normalized.percent_stake = request.percent_stake ?? null;
    normalized.kelly_fraction = null;
  } else if (request.staking_method === "kelly") {
    normalized.fixed_stake = null;
    normalized.percent_stake = null;
    normalized.kelly_fraction = request.kelly_fraction ?? null;
  }

  if (normalized.period_mode !== "custom") {
    normalized.custom_periods = null;
    normalized.reset_bankroll_each_period = false;
    normalized.max_candidates_per_period = null;
    normalized.rank_by = null;
    normalized.rank_order = "asc";
    normalized.require_full_candidate_count = false;
  }

  if (!normalized.walk_forward) {
    normalized.train_window_matches = null;
    normalized.test_window_matches = null;
    normalized.step_matches = null;
  }

  return normalized;
}

export default function DatasetDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>();

  const [data, setData] = useState<DatasetIntrospection | null>(null);
  const [mapping, setMapping] = useState<DatasetMapping>(buildInitialMapping());
  const [request, setRequest] = useState<SimulationRequest>(
    buildInitialSimulationRequest()
  );
  const [persist, setPersist] = useState(true);

  const [leagueOptions, setLeagueOptions] = useState<string[]>([]);
  const [seasonOptions, setSeasonOptions] = useState<string[]>([]);

  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [sweeping, setSweeping] = useState(false);
  const [sweepPersistRuns, setSweepPersistRuns] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [sweepResult, setSweepResult] = useState<DatasetSweepResponse | null>(
    null
  );

  const [loadedDraftInfo, setLoadedDraftInfo] = useState<{
    sourceRunId?: string | null;
    savedAt?: string | null;
  } | null>(null);

  const hasHydratedRef = useRef(false);

  useEffect(() => {
    async function load() {
      if (!datasetId) return;

      setLoading(true);
      setError(null);
      hasHydratedRef.current = false;

      try {
        const introspection = await introspectDataset(datasetId);
        setData(introspection);

        const cols = introspection.columns;
        const defaultLeagueCol = cols.includes("League") ? "League" : null;
        const defaultSeasonCol = cols.includes("Season") ? "Season" : null;
        const defaultResultCol = cols.includes("FTR")
          ? "FTR"
          : cols.includes("result")
          ? "result"
          : null;

        const draft = loadSimulationDraft(datasetId);

        if (draft) {
          setMapping(draft.mapping);
          setRequest(normalizeRequest(draft.request));
          setPersist(draft.persist ?? true);
          setLoadedDraftInfo({
            sourceRunId: draft.sourceRunId ?? null,
            savedAt: draft.savedAt ?? null,
          });
        } else {
          setMapping((prev) => ({
            ...prev,
            league_col: prev.league_col ?? defaultLeagueCol,
            season_col: prev.season_col ?? defaultSeasonCol,
            result_col: prev.result_col ?? defaultResultCol,
          }));
          setPersist(true);
          setLoadedDraftInfo(null);
        }

        hasHydratedRef.current = true;
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dataset details"
        );
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [datasetId]);

  useEffect(() => {
    async function loadLeagueOptions() {
      if (!datasetId || !mapping.league_col) {
        setLeagueOptions([]);
        return;
      }

      try {
        const res = await getDistinctValues(datasetId, mapping.league_col);
        setLeagueOptions(res.values);
      } catch (err) {
        console.error("Failed to load league options", err);
        setLeagueOptions([]);
      }
    }

    void loadLeagueOptions();
  }, [datasetId, mapping.league_col]);

  useEffect(() => {
    async function loadSeasonOptions() {
      if (!datasetId || !mapping.season_col) {
        setSeasonOptions([]);
        return;
      }

      try {
        const res = await getDistinctValues(datasetId, mapping.season_col);
        setSeasonOptions(res.values);

        if (res.values.length === 1) {
          setRequest((prev) =>
            normalizeRequest({
              ...prev,
              season: prev.season || res.values[0],
            })
          );
        }
      } catch (err) {
        console.error("Failed to load season options", err);
        setSeasonOptions([]);
      }
    }

    void loadSeasonOptions();
  }, [datasetId, mapping.season_col]);

  useEffect(() => {
    if (!datasetId || !hasHydratedRef.current) return;

    saveSimulationDraft(datasetId, {
      sourceRunId: loadedDraftInfo?.sourceRunId ?? null,
      mapping,
      request: normalizeRequest(request),
      persist,
    });
  }, [datasetId, mapping, request, persist, loadedDraftInfo]);

  const availableNames = useMemo(() => {
    const builtins = [
      "home_team",
      "away_team",
      "home_goals",
      "away_goals",
      "home_win_odds",
      "draw_odds",
      "away_win_odds",
      "model_home_prob",
      "model_draw_prob",
      "model_away_prob",
      "home_win_rate",
      "away_win_rate",
      "home_points",
      "away_points",
      "home_goal_diff",
      "away_goal_diff",
      "points_diff",
      "goal_diff_diff",
      "edge",
    ];

    const featureNames = mapping.feature_cols ?? [];
    return Array.from(new Set([...builtins, ...featureNames])).sort();
  }, [mapping.feature_cols]);

  const rankFieldOptions = useMemo(() => {
    const builtins = ["edge"];
    return Array.from(
      new Set([...(mapping.feature_cols ?? []), ...builtins])
    ).sort();
  }, [mapping.feature_cols]);

  async function handleSimulate() {
    if (!datasetId) return;

    if (!request.selection) {
      setError("Selection is required.");
      return;
    }

    setSimulating(true);
    setError(null);
    setResult(null);

    try {
      const res = await simulateDataset(datasetId, {
        mapping,
        request: normalizeRequest(request),
        persist,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setSimulating(false);
    }
  }

  async function handleRunSweep(
    grid: Record<string, unknown[]>,
    persistRuns: boolean
  ) {
    if (!datasetId) return;

    if (!request.selection) {
      setError("Selection is required.");
      return;
    }

    setSweeping(true);
    setError(null);
    setSweepResult(null);

    try {
      const res = await runDatasetSweep(datasetId, {
        mapping,
        base_request: normalizeRequest(request),
        grid,
        persist_runs: persistRuns,
      });
      setSweepResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sweep failed");
    } finally {
      setSweeping(false);
    }
  }

  function handleClearLoadedDraft() {
    if (!datasetId) return;

    clearSimulationDraft(datasetId);
    setLoadedDraftInfo(null);
    setMapping(buildInitialMapping());
    setRequest(buildInitialSimulationRequest());
    setPersist(true);
    setResult(null);
    setSweepResult(null);
  }

  if (!datasetId) {
    return <div>Missing dataset id.</div>;
  }

  if (loading) {
    return <div>Loading dataset...</div>;
  }

  if (error && !data) {
    return <div style={{ color: "#b00020" }}>{error}</div>;
  }

  if (!data) {
    return <div>No dataset data available.</div>;
  }

  const sampleRows = data.sample_rows.slice(0, 3);

  return (
    <div style={{ display: "grid", gap: 20, minWidth: 0 }}>
      <SectionPanel title="Dataset overview">
        <div style={{ display: "grid", gap: 6 }}>
          <div>
            <strong>Filename:</strong> {data.filename}
          </div>
          <div>
            <strong>Dataset ID:</strong> {data.dataset_id}
          </div>
          <div>
            <strong>Columns:</strong> {data.columns.length}
          </div>
          <div>
            <strong>Preview rows:</strong> {sampleRows.length}
          </div>
        </div>
      </SectionPanel>

      {loadedDraftInfo && (
        <section
          style={{
            border: "1px solid #cfe3ff",
            borderRadius: 10,
            padding: 16,
            background: "#eef6ff",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 12,
              alignItems: "start",
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "grid", gap: 6 }}>
              <div style={{ fontWeight: 600 }}>Loaded simulator draft</div>
              {loadedDraftInfo.sourceRunId && (
                <div>
                  <strong>Source run:</strong> {loadedDraftInfo.sourceRunId}
                </div>
              )}
              {loadedDraftInfo.savedAt && (
                <div>
                  <strong>Saved at:</strong> {loadedDraftInfo.savedAt}
                </div>
              )}
            </div>

            <button onClick={handleClearLoadedDraft}>Clear loaded draft</button>
          </div>
        </section>
      )}

      {error && <div style={{ color: "#b00020" }}>{error}</div>}

      <SectionPanel title="Columns">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 8,
          }}
        >
          {data.columns.map((col, idx) => (
            <div
              key={`${col}-${idx}`}
              style={{
                border: "1px solid #ddd",
                borderRadius: 6,
                padding: 10,
                background: "#fafafa",
              }}
            >
              <div style={{ fontWeight: 600 }}>{col}</div>
              <div style={{ fontSize: 12, color: "#666" }}>
                {data.inferred_types[col] ?? "unknown"}
              </div>
            </div>
          ))}
        </div>
      </SectionPanel>

      <SectionPanel title="Sample rows">
        {sampleRows.length === 0 ? (
          <div>No sample rows available.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {data.columns.map((col, idx) => (
                    <th key={`${col}-${idx}`} style={thStyle}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sampleRows.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {data.columns.map((col, colIdx) => (
                      <td key={`${col}-${colIdx}`} style={tdStyle}>
                        {row[col] ?? ""}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionPanel>

      <SectionPanel title="Column mapping">
        <MappingForm columns={data.columns} value={mapping} onChange={setMapping} />
      </SectionPanel>

      <SectionPanel title="Simulation setup">
        <SimulationForm
          value={request}
          onChange={(next) => setRequest(normalizeRequest(next))}
          onSubmit={handleSimulate}
          submitting={simulating}
          persist={persist}
          onPersistChange={setPersist}
          leagueOptions={leagueOptions}
          seasonOptions={seasonOptions}
          rankFieldOptions={rankFieldOptions}
        />
      </SectionPanel>

      <SectionPanel title="Parameter sweep">
        <SweepForm
          availableFields={rankFieldOptions}
          persistRuns={sweepPersistRuns}
          onPersistRunsChange={setSweepPersistRuns}
          onSubmit={handleRunSweep}
          submitting={sweeping}
        />
      </SectionPanel>

      <SectionPanel title="Sweep results">
        <SweepResultsView result={sweepResult} />
      </SectionPanel>

      <SectionPanel title="Rule builder">
        <RuleEditor
          expression={request.rule_expression ?? ""}
          onChange={(value) =>
            setRequest((prev) =>
              normalizeRequest({
                ...prev,
                rule_expression: value,
              })
            )
          }
          availableNames={availableNames}
        />
      </SectionPanel>

      <SectionPanel title="Results">
        <SimulationResultView result={result} />
      </SectionPanel>
    </div>
  );
}

function SectionPanel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section
      style={{
        border: "1px solid #ddd",
        borderRadius: 10,
        padding: 16,
        background: "#fff",
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: 16 }}>{title}</h3>
      {children}
    </section>
  );
}

const thStyle: CSSProperties = {
  textAlign: "left",
  borderBottom: "1px solid #ddd",
  padding: "8px 12px",
  whiteSpace: "nowrap",
};

const tdStyle: CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "8px 12px",
  whiteSpace: "nowrap",
};