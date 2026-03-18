import type { CustomPeriodDefinition, DayKey } from "../types/api";

type Props = {
  value: CustomPeriodDefinition[];
  onChange: (next: CustomPeriodDefinition[]) => void;
  disabled?: boolean;
};

const DAY_OPTIONS: { value: DayKey; label: string }[] = [
  { value: "mon", label: "Monday" },
  { value: "tue", label: "Tuesday" },
  { value: "wed", label: "Wednesday" },
  { value: "thu", label: "Thursday" },
  { value: "fri", label: "Friday" },
  { value: "sat", label: "Saturday" },
  { value: "sun", label: "Sunday" },
];

const controlStyle: React.CSSProperties = {
  padding: 8,
  width: "100%",
  minWidth: 0,
};

function buildEmptyPeriod(): CustomPeriodDefinition {
  return {
    name: "",
    start_day: "fri",
    end_day: "mon",
  };
}

export default function CustomPeriodBuilder({
  value,
  onChange,
  disabled = false,
}: Props) {
  function updatePeriod(
    index: number,
    patch: Partial<CustomPeriodDefinition>
  ) {
    const next = value.map((period, idx) =>
      idx === index ? { ...period, ...patch } : period
    );
    onChange(next);
  }

  function addPeriod() {
    onChange([...(value ?? []), buildEmptyPeriod()]);
  }

  function removePeriod(index: number) {
    onChange(value.filter((_, idx) => idx !== index));
  }

  return (
    <div style={{ display: "grid", gap: 12, width: "100%", minWidth: 0 }}>
      {(value ?? []).map((period, index) => (
        <div
          key={`custom-period-${index}`}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 8,
            alignItems: "end",
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 12,
            background: "#fafafa",
            width: "100%",
            maxWidth: "100%",
            minWidth: 0,
          }}
        >
          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Name</span>
            <input
              value={period.name}
              onChange={(e) => updatePeriod(index, { name: e.target.value })}
              placeholder="Weekend"
              disabled={disabled}
              style={controlStyle}
            />
          </label>

          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>Start day</span>
            <select
              value={period.start_day}
              onChange={(e) =>
                updatePeriod(index, {
                  start_day: e.target.value as DayKey,
                })
              }
              disabled={disabled}
              style={controlStyle}
            >
              {DAY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 4, minWidth: 0 }}>
            <span>End day</span>
            <select
              value={period.end_day}
              onChange={(e) =>
                updatePeriod(index, {
                  end_day: e.target.value as DayKey,
                })
              }
              disabled={disabled}
              style={controlStyle}
            >
              {DAY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div style={{ display: "flex", alignItems: "end" }}>
            <button
              type="button"
              onClick={() => removePeriod(index)}
              disabled={disabled}
              style={{ padding: "8px 12px" }}
            >
              Remove
            </button>
          </div>
        </div>
      ))}

      <div>
        <button type="button" onClick={addPeriod} disabled={disabled}>
          Add period
        </button>
      </div>
    </div>
  );
}
