import { useMemo } from "react";

import type {
  CustomPeriodDefinition,
  SimulationRequest,
} from "../../types/api";
import CustomPeriodBuilder from "../CustomPeriodBuilder";

type Props = {
  value: SimulationRequest;
  onChange: (next: SimulationRequest) => void;
  onSubmit: () => void;
  submitting: boolean;
  persist: boolean;
  onPersistChange: (value: boolean) => void;
  leagueOptions?: string[];
  seasonOptions?: string[];
  rankFieldOptions?: string[];
};

const DEFAULT_CUSTOM_PERIODS: CustomPeriodDefinition[] = [
  { name: "Weekend", start_day: "fri", end_day: "mon" },
  { name: "Midweek", start_day: "tue", end_day: "thu" },
];

function validateCustomPeriods(periods: CustomPeriodDefinition[]): string[] {
  const errors: string[] = [];

  if (!periods.length) {
    errors.push("Add at least one custom period.");
    return errors;
  }

  const normalizedNames = periods.map((period) => period.name.trim().toLowerCase());

  if (normalizedNames.some((name) => name.length === 0)) {
    errors.push("Each custom period must have a name.");
  }

  const nonEmptyNames = normalizedNames.filter((name) => name.length > 0);
  if (new Set(nonEmptyNames).size !== nonEmptyNames.length) {
    errors.push("Custom period names must be unique.");
  }

  return errors;
}


const controlStyle: React.CSSProperties = {
  padding: 8,
  width: "100%",
  minWidth: 0,
};

export default function SimulationForm({
  value,
  onChange,
  onSubmit,
  submitting,
  persist,
  onPersistChange,
  leagueOptions = [],
  seasonOptions = [],
  rankFieldOptions = [],
}: Props) {
  const customPeriodErrors = useMemo(
    () =>
      value.period_mode === "custom"
        ? validateCustomPeriods(value.custom_periods ?? [])
        : [],
    [value.period_mode, value.custom_periods]
  );

  function setField<K extends keyof SimulationRequest>(
    key: K,
    fieldValue: SimulationRequest[K]
  ) {
    onChange({
      ...value,
      [key]: fieldValue,
    });
  }

  function toggleLeague(league: string) {
    const current = value.leagues ?? [];
    const exists = current.includes(league);

    const nextLeagues = exists
      ? current.filter((l) => l !== league)
      : [...current, league];

    onChange({
      ...value,
      league: nextLeagues.length === 1 ? nextLeagues[0] : undefined,
      leagues: nextLeagues,
    });
  }

  function handlePeriodModeChange(mode: "none" | "custom") {
    if (mode === "none") {
      onChange({
        ...value,
        period_mode: "none",
        custom_periods: undefined,
        reset_bankroll_each_period: false,
        max_candidates_per_period: undefined,
        rank_by: undefined,
        rank_order: "asc",
        require_full_candidate_count: false,
      });
      return;
    }

    onChange({
      ...value,
      period_mode: "custom",
      custom_periods:
        value.custom_periods && value.custom_periods.length > 0
          ? value.custom_periods
          : DEFAULT_CUSTOM_PERIODS,
      rank_order: value.rank_order ?? "asc",
    });
  }

  function handleCustomPeriodsChange(custom_periods: CustomPeriodDefinition[]) {
    onChange({
      ...value,
      custom_periods,
    });
  }

  function handleSubmit() {
    if (customPeriodErrors.length > 0) {
      return;
    }
    onSubmit();
  }

  return (
    <div style={{ display: "grid", gap: 16, width: "100%", minWidth: 0 }}>
      <div style={gridStyle}>
        {seasonOptions.length > 0 ? (
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Season</span>
            <select
              value={value.season}
              onChange={(e) => setField("season", e.target.value)}
              style={controlStyle}
            >
              <option value="">-- select season --</option>
              {seasonOptions.map((season, idx) => (
                <option key={`${season}-${idx}`} value={season}>
                  {season}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Season</span>
            <input
              value={value.season}
              onChange={(e) => setField("season", e.target.value)}
              style={controlStyle}
            />
          </label>
        )}

        <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
          <span>Selection</span>
          <select
            value={value.selection ?? ""}
            onChange={(e) =>
              setField(
                "selection",
                (e.target.value || null) as "H" | "D" | "A" | null
              )
            }
            style={controlStyle}
          >
            <option value="">-- select --</option>
            <option value="H">H</option>
            <option value="D">D</option>
            <option value="A">A</option>
          </select>
        </label>

        <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
          <span>Staking method</span>
          <select
            value={value.staking_method}
            onChange={(e) =>
              setField(
                "staking_method",
                e.target.value as SimulationRequest["staking_method"]
              )
            }
            style={controlStyle}
          >
            <option value="fixed">fixed</option>
            <option value="percent">percent</option>
            <option value="kelly">kelly</option>
          </select>
        </label>

        {value.staking_method === "fixed" && (
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Fixed stake</span>
            <input
              type="number"
              value={value.fixed_stake ?? ""}
              onChange={(e) =>
                setField(
                  "fixed_stake",
                  e.target.value === "" ? null : Number(e.target.value)
                )
              }
              style={controlStyle}
            />
          </label>
        )}

        {value.staking_method === "percent" && (
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Percent stake</span>
            <input
              type="number"
              step="0.01"
              value={value.percent_stake ?? ""}
              onChange={(e) =>
                setField(
                  "percent_stake",
                  e.target.value === "" ? null : Number(e.target.value)
                )
              }
              style={controlStyle}
            />
          </label>
        )}

        {value.staking_method === "kelly" && (
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Kelly fraction</span>
            <input
              type="number"
              step="0.01"
              value={value.kelly_fraction ?? ""}
              onChange={(e) =>
                setField(
                  "kelly_fraction",
                  e.target.value === "" ? null : Number(e.target.value)
                )
              }
              style={controlStyle}
            />
          </label>
        )}

        <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
          <span>Starting bankroll</span>
          <input
            type="number"
            value={value.starting_bankroll}
            onChange={(e) =>
              setField("starting_bankroll", Number(e.target.value))
            }
            style={controlStyle}
          />
        </label>

        <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
          <span>Multiple legs</span>
          <input
            type="number"
            min={1}
            value={value.multiple_legs}
            onChange={(e) => setField("multiple_legs", Number(e.target.value))}
            style={controlStyle}
          />
        </label>

        <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
          <span>Min odds</span>
          <input
            type="number"
            step="0.01"
            value={value.min_odds ?? ""}
            onChange={(e) =>
              setField(
                "min_odds",
                e.target.value === "" ? null : Number(e.target.value)
              )
            }
            style={controlStyle}
          />
        </label>
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <strong>Leagues</strong>

        {leagueOptions.length > 0 ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 8,
              width: "100%",
              maxWidth: "100%",
              minWidth: 0,
            }}
          >
            {leagueOptions.map((league, idx) => {
              const checked = (value.leagues ?? []).includes(league);

              return (
                <label
                  key={`${league}-${idx}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    border: "1px solid #ddd",
                    borderRadius: 6,
                    padding: "6px 8px",
                    background: checked ? "#eef6ff" : "#fff",
                    minWidth: 0,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleLeague(league)}
                  />
                  <span style={{ overflowWrap: "anywhere", wordBreak: "break-word" }}>{league}</span>
                </label>
              );
            })}
          </div>
        ) : (
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Leagues (comma-separated)</span>
            <input
              value={(value.leagues ?? []).join(", ")}
              onChange={(e) => {
                const leagues = e.target.value
                  .split(",")
                  .map((s) => s.trim())
                  .filter((s) => s.length > 0);

                onChange({
                  ...value,
                  league: leagues.length === 1 ? leagues[0] : undefined,
                  leagues,
                });
              }}
              placeholder="Premier-League, Championship"
              style={controlStyle}
            />
          </label>
        )}
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={value.walk_forward ?? false}
            onChange={(e) => setField("walk_forward", e.target.checked)}
          />
          <span>Enable walk-forward validation</span>
        </label>

        {value.walk_forward && (
          <div style={gridStyle}>
            <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
              <span>Train window matches</span>
              <input
                type="number"
                value={value.train_window_matches ?? ""}
                onChange={(e) =>
                  setField(
                    "train_window_matches",
                    e.target.value === "" ? null : Number(e.target.value)
                  )
                }
                style={controlStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
              <span>Test window matches</span>
              <input
                type="number"
                value={value.test_window_matches ?? ""}
                onChange={(e) =>
                  setField(
                    "test_window_matches",
                    e.target.value === "" ? null : Number(e.target.value)
                  )
                }
                style={controlStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
              <span>Step matches</span>
              <input
                type="number"
                value={value.step_matches ?? ""}
                onChange={(e) =>
                  setField(
                    "step_matches",
                    e.target.value === "" ? null : Number(e.target.value)
                  )
                }
                style={controlStyle}
              />
            </label>
          </div>
        )}
      </div>

      <div style={{ display: "grid", gap: 12 }}>
        <strong>Calendar betting mode</strong>

        <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
          <span>Period mode</span>
          <select
            value={value.period_mode ?? "none"}
            onChange={(e) =>
              handlePeriodModeChange(e.target.value as "none" | "custom")
            }
            style={{ ...controlStyle, maxWidth: 320 }}
          >
            <option value="none">none</option>
            <option value="custom">custom weekly periods</option>
          </select>
        </label>

        {value.period_mode === "custom" && (
          <div style={{ display: "grid", gap: 12 }}>
            <CustomPeriodBuilder
              value={value.custom_periods ?? []}
              onChange={handleCustomPeriodsChange}
              disabled={submitting}
            />

            {customPeriodErrors.length > 0 && (
              <div
                style={{
                  border: "1px solid #f0c36d",
                  borderRadius: 8,
                  padding: 12,
                  background: "#fff7e6",
                  color: "#7a4d00",
                }}
              >
                {customPeriodErrors.map((error, index) => (
                  <div key={`custom-period-error-${index}`}>{error}</div>
                ))}
              </div>
            )}

            <div style={gridStyle}>
              <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
                <span>Max candidates per period</span>
                <input
                  type="number"
                  min={1}
                  value={value.max_candidates_per_period ?? ""}
                  onChange={(e) =>
                    setField(
                      "max_candidates_per_period",
                      e.target.value === "" ? null : Number(e.target.value)
                    )
                  }
                  style={controlStyle}
                />
              </label>

              <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
                <span>Rank by</span>
                <select
                  value={value.rank_by ?? ""}
                  onChange={(e) => setField("rank_by", e.target.value || null)}
                  style={controlStyle}
                >
                  <option value="">-- none --</option>
                  {rankFieldOptions.map((field, idx) => (
                    <option key={`${field}-${idx}`} value={field}>
                      {field}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
                <span>Rank order</span>
                <select
                  value={value.rank_order ?? "asc"}
                  onChange={(e) =>
                    setField("rank_order", e.target.value as "asc" | "desc")
                  }
                  style={controlStyle}
                >
                  <option value="asc">ascending</option>
                  <option value="desc">descending</option>
                </select>
              </label>
            </div>

            <div style={{ display: "grid", gap: 8 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={value.require_full_candidate_count ?? false}
                  onChange={(e) =>
                    setField("require_full_candidate_count", e.target.checked)
                  }
                />
                <span>Skip period unless full candidate count is available</span>
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={value.reset_bankroll_each_period ?? false}
                  onChange={(e) =>
                    setField("reset_bankroll_each_period", e.target.checked)
                  }
                />
                <span>Reset bankroll for each period</span>
              </label>
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={persist}
            onChange={(e) => onPersistChange(e.target.checked)}
          />
          <span>Persist run</span>
        </label>
      </div>

      <div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || customPeriodErrors.length > 0}
        >
          {submitting ? "Running..." : "Run simulation"}
        </button>
      </div>
    </div>
  );
}

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
  width: "100%",
  maxWidth: "100%",
  minWidth: 0,
};
