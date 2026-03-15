import { useMemo, useState } from "react";

type SweepRow = {
  field: string;
  values: string;
};

type Props = {
  availableFields: string[];
  persistRuns: boolean;
  onPersistRunsChange: (value: boolean) => void;
  onSubmit: (grid: Record<string, unknown[]>, persistRuns: boolean) => void;
  submitting: boolean;
};

const DEFAULT_ROWS: SweepRow[] = [];

export default function SweepForm({
  availableFields,
  persistRuns,
  onPersistRunsChange,
  onSubmit,
  submitting,
}: Props) {
  const [rows, setRows] = useState<SweepRow[]>(DEFAULT_ROWS);

  const fieldOptions = useMemo(() => {
    return [
      "multiple_legs",
      "max_candidates_per_period",
      "rank_order",
      "fixed_stake",
      "require_full_candidate_count",
      "rule_expression",
      ...availableFields.filter(
        (f) =>
          ![
            "multiple_legs",
            "max_candidates_per_period",
            "rank_order",
            "fixed_stake",
            "require_full_candidate_count",
            "rule_expression",
          ].includes(f)
      ),
    ];
  }, [availableFields]);

  function updateRow(index: number, patch: Partial<SweepRow>) {
    setRows((prev) =>
      prev.map((row, i) => (i === index ? { ...row, ...patch } : row))
    );
  }

  function addRow() {
    setRows((prev) => [...prev, { field: "", values: "" }]);
  }

  function removeRow(index: number) {
    setRows((prev) => prev.filter((_, i) => i !== index));
  }

  function clearRows() {
    setRows([]);
  }

  function parseValue(raw: string): unknown {
    const trimmed = raw.trim();

    if (trimmed === "") return trimmed;
    if (trimmed === "true") return true;
    if (trimmed === "false") return false;

    const asNumber = Number(trimmed);
    if (!Number.isNaN(asNumber) && trimmed !== "") {
      return asNumber;
    }

    return trimmed;
  }

  function buildGrid(): Record<string, unknown[]> {
    const grid: Record<string, unknown[]> = {};

    for (const row of rows) {
      const field = row.field.trim();
      if (!field) continue;

      const values = row.values
        .split(",")
        .map((v) => v.trim())
        .filter((v) => v.length > 0)
        .map(parseValue);

      if (values.length === 0) continue;

      const existing = grid[field] ?? [];
      grid[field] = Array.from(new Set([...existing, ...values]));
    }

    return grid;
  }

  function handleSubmit() {
    onSubmit(buildGrid(), persistRuns);
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ color: "#666", fontSize: 14 }}>
        Define one or more parameter grids to run many variants of the current
        simulation setup.
      </div>

      {rows.length === 0 ? (
        <div
          style={{
            border: "1px dashed #ccc",
            borderRadius: 8,
            padding: 16,
            color: "#666",
            background: "#fafafa",
          }}
        >
          No sweep fields added yet.
        </div>
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          {rows.map((row, index) => (
            <div
              key={index}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(220px, 280px) 1fr auto",
                gap: 12,
                alignItems: "end",
              }}
            >
              <label style={{ display: "grid", gap: 4 }}>
                <span>Field</span>
                <select
                  value={row.field}
                  onChange={(e) => updateRow(index, { field: e.target.value })}
                  style={{ padding: 8 }}
                >
                  <option value="">-- select field --</option>
                  {fieldOptions.map((field, idx) => (
                    <option key={`${field}-${idx}`} value={field}>
                      {field}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ display: "grid", gap: 4 }}>
                <span>Values (comma-separated)</span>
                <input
                  value={row.values}
                  onChange={(e) => updateRow(index, { values: e.target.value })}
                  placeholder="e.g. 2,4,6 or asc,desc or PPIDiff < 0.05, PPIDiff < 0.1"
                  style={{ padding: 8 }}
                />
              </label>

              <button type="button" onClick={() => removeRow(index)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button type="button" onClick={addRow}>
          Add sweep field
        </button>

        <button type="button" onClick={clearRows} disabled={rows.length === 0}>
          Clear sweep fields
        </button>

        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={persistRuns}
            onChange={(e) => onPersistRunsChange(e.target.checked)}
          />
          <span>Persist sweep variants as runs</span>
        </label>
      </div>

      <div>
        <button type="button" onClick={handleSubmit} disabled={submitting}>
          {submitting ? "Running sweep..." : "Run sweep"}
        </button>
      </div>
    </div>
  );
}