import type { DatasetMapping } from "../../types/api";

type Props = {
  columns: string[];
  value: DatasetMapping;
  onChange: (next: DatasetMapping) => void;
};

type MappingKey = keyof DatasetMapping;

function SelectField({
  label,
  columns,
  value,
  onChange,
  allowEmpty = true,
}: {
  label: string;
  columns: string[];
  value?: string | null;
  onChange: (value: string | null) => void;
  allowEmpty?: boolean;
}) {
  return (
    <label style={{ display: "grid", gap: 4 }}>
      <span>{label}</span>
      <select
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value || null)}
        style={{ padding: 8 }}
      >
        {allowEmpty && <option value="">-- none --</option>}
        {columns.map((col, idx) => (
          <option key={`${col}-${idx}`} value={col}>
            {col}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function MappingForm({ columns, value, onChange }: Props) {
  function setField<K extends MappingKey>(key: K, fieldValue: DatasetMapping[K]) {
    onChange({
      ...value,
      [key]: fieldValue,
    });
  }

  function toggleFeature(col: string) {
    const exists = value.feature_cols.includes(col);
    const next = exists
      ? value.feature_cols.filter((c) => c !== col)
      : [...value.feature_cols, col];

    setField("feature_cols", next);
  }

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <div style={gridStyle}>
        <SelectField
          label="Home team column *"
          columns={columns}
          value={value.home_team_col}
          onChange={(v) => setField("home_team_col", v ?? "")}
          allowEmpty={false}
        />

        <SelectField
          label="Away team column *"
          columns={columns}
          value={value.away_team_col}
          onChange={(v) => setField("away_team_col", v ?? "")}
          allowEmpty={false}
        />

        <SelectField
          label="Date column *"
          columns={columns}
          value={value.date_col}
          onChange={(v) => setField("date_col", v ?? "")}
          allowEmpty={false}
        />

        <SelectField
          label="Time column"
          columns={columns}
          value={value.time_col}
          onChange={(v) => setField("time_col", v)}
        />

        <label style={{ display: "grid", gap: 4 }}>
          <span>Date format</span>
          <input
            value={value.date_format ?? ""}
            onChange={(e) => setField("date_format", e.target.value || null)}
            placeholder="%Y-%m-%d"
            style={{ padding: 8 }}
          />
        </label>

        <label style={{ display: "grid", gap: 4 }}>
          <span>Time format</span>
          <input
            value={value.time_format ?? ""}
            onChange={(e) => setField("time_format", e.target.value || null)}
            placeholder="%H:%M"
            style={{ padding: 8 }}
          />
        </label>

        <SelectField
          label="League column"
          columns={columns}
          value={value.league_col}
          onChange={(v) => setField("league_col", v)}
        />

        <SelectField
          label="Season column"
          columns={columns}
          value={value.season_col}
          onChange={(v) => setField("season_col", v)}
        />

        <SelectField
          label="Result column"
          columns={columns}
          value={value.result_col}
          onChange={(v) => setField("result_col", v)}
        />

        <SelectField
          label="Home goals column"
          columns={columns}
          value={value.home_goals_col}
          onChange={(v) => setField("home_goals_col", v)}
        />

        <SelectField
          label="Away goals column"
          columns={columns}
          value={value.away_goals_col}
          onChange={(v) => setField("away_goals_col", v)}
        />

        <SelectField
          label="Home odds column"
          columns={columns}
          value={value.odds_home_col}
          onChange={(v) => setField("odds_home_col", v)}
        />

        <SelectField
          label="Draw odds column"
          columns={columns}
          value={value.odds_draw_col}
          onChange={(v) => setField("odds_draw_col", v)}
        />

        <SelectField
          label="Away odds column"
          columns={columns}
          value={value.odds_away_col}
          onChange={(v) => setField("odds_away_col", v)}
        />

        <SelectField
          label="Model home prob column"
          columns={columns}
          value={value.model_home_prob_col}
          onChange={(v) => setField("model_home_prob_col", v)}
        />

        <SelectField
          label="Model draw prob column"
          columns={columns}
          value={value.model_draw_prob_col}
          onChange={(v) => setField("model_draw_prob_col", v)}
        />

        <SelectField
          label="Model away prob column"
          columns={columns}
          value={value.model_away_prob_col}
          onChange={(v) => setField("model_away_prob_col", v)}
        />
      </div>

      <div>
        <h4 style={{ marginTop: 0, marginBottom: 8 }}>Feature columns</h4>
        <div style={featureGridStyle}>
          {columns.map((col, idx) => (
            <label key={`${col}-${idx}`}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                border: "1px solid #ddd",
                borderRadius: 6,
                padding: "6px 8px",
                background: value.feature_cols.includes(col) ? "#eef6ff" : "#fff",
              }}
            >
              <input
                type="checkbox"
                checked={value.feature_cols.includes(col)}
                onChange={() => toggleFeature(col)}
              />
              <span>{col}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 12,
};

const featureGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 8,
};