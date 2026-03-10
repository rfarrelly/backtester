import type { SimulationRequest } from "../../types/api";

type Props = {
  value: SimulationRequest;
  onChange: (next: SimulationRequest) => void;
  onSubmit: () => void;
  submitting: boolean;
  persist: boolean;
  onPersistChange: (value: boolean) => void;
};

export default function SimulationForm({
  value,
  onChange,
  onSubmit,
  submitting,
  persist,
  onPersistChange,
}: Props) {
  function setField<K extends keyof SimulationRequest>(key: K, fieldValue: SimulationRequest[K]) {
    onChange({
      ...value,
      [key]: fieldValue,
    });
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={gridStyle}>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Leagues (comma-separated)</span>
          <input
            value={(value.leagues ?? []).join(", ")}
            onChange={(e) => {
              const leagues = e.target.value
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean);

              onChange({
                ...value,
                league: leagues.length === 1 ? leagues[0] : null,
                leagues,
              });
            }}
            placeholder="Premier-League, Championship"
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Season</span>
          <input
            value={value.season}
            onChange={(e) => setField("season", e.target.value)}
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Strategy type</span>
          <select
            value={value.strategy_type}
            onChange={(e) =>
              setField("strategy_type", e.target.value as SimulationRequest["strategy_type"])
            }
            style={{ padding: 8 }}
          >
            <option value="home">home</option>
            <option value="edge">edge</option>
            <option value="rules">rules</option>
          </select>
        </label>

        {(value.strategy_type === "edge" || value.strategy_type === "rules") && (
          <label style={{ display: "grid", gap: 4 }}>
            <span>Selection</span>
            <select
              value={value.selection ?? ""}
              onChange={(e) =>
                setField("selection", (e.target.value || null) as "H" | "D" | "A" | null)
              }
              style={{ padding: 8 }}
            >
              <option value="">-- select --</option>
              <option value="H">H</option>
              <option value="D">D</option>
              <option value="A">A</option>
            </select>
          </label>
        )}

        {value.strategy_type === "edge" && (
          <label style={{ display: "grid", gap: 4 }}>
            <span>Min edge</span>
            <input
              type="number"
              step="0.01"
              value={value.min_edge ?? ""}
              onChange={(e) =>
                setField("min_edge", e.target.value === "" ? null : Number(e.target.value))
              }
              style={{ padding: 8 }}
            />
          </label>
        )}

        <label style={{ display: "grid", gap: 4 }}>
          <span>Staking method</span>
          <select
            value={value.staking_method}
            onChange={(e) =>
              setField("staking_method", e.target.value as SimulationRequest["staking_method"])
            }
            style={{ padding: 8 }}
          >
            <option value="fixed">fixed</option>
            <option value="percent">percent</option>
            <option value="kelly">kelly</option>
          </select>
        </label>

        {value.staking_method === "fixed" && (
          <label style={{ display: "grid", gap: 4 }}>
            <span>Fixed stake</span>
            <input
              type="number"
              value={value.fixed_stake ?? ""}
              onChange={(e) =>
                setField("fixed_stake", e.target.value === "" ? null : Number(e.target.value))
              }
              style={{ padding: 8 }}
            />
          </label>
        )}

        {value.staking_method === "percent" && (
          <label style={{ display: "grid", gap: 4 }}>
            <span>Percent stake</span>
            <input
              type="number"
              step="0.01"
              value={value.percent_stake ?? ""}
              onChange={(e) =>
                setField("percent_stake", e.target.value === "" ? null : Number(e.target.value))
              }
              style={{ padding: 8 }}
            />
          </label>
        )}

        {value.staking_method === "kelly" && (
          <label style={{ display: "grid", gap: 4 }}>
            <span>Kelly fraction</span>
            <input
              type="number"
              step="0.01"
              value={value.kelly_fraction ?? ""}
              onChange={(e) =>
                setField("kelly_fraction", e.target.value === "" ? null : Number(e.target.value))
              }
              style={{ padding: 8 }}
            />
          </label>
        )}

        <label style={{ display: "grid", gap: 4 }}>
          <span>Starting bankroll</span>
          <input
            type="number"
            value={value.starting_bankroll}
            onChange={(e) => setField("starting_bankroll", Number(e.target.value))}
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Multiple legs</span>
          <input
            type="number"
            min={1}
            value={value.multiple_legs}
            onChange={(e) => setField("multiple_legs", Number(e.target.value))}
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Min odds</span>
          <input
            type="number"
            step="0.01"
            value={value.min_odds ?? ""}
            onChange={(e) =>
              setField("min_odds", e.target.value === "" ? null : Number(e.target.value))
            }
            style={{ padding: 8 }}
          />
        </label>
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
            <label style={{ display: "grid", gap: 4 }}>
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
                style={{ padding: 8 }}
              />
            </label>

            <label style={{ display: "grid", gap: 4 }}>
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
                style={{ padding: 8 }}
              />
            </label>

            <label style={{ display: "grid", gap: 4 }}>
              <span>Step matches</span>
              <input
                type="number"
                value={value.step_matches ?? ""}
                onChange={(e) =>
                  setField("step_matches", e.target.value === "" ? null : Number(e.target.value))
                }
                style={{ padding: 8 }}
              />
            </label>
          </div>
        )}

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
        <button onClick={onSubmit} disabled={submitting}>
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
};