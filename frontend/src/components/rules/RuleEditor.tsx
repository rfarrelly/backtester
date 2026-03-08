import { useState } from "react";
import { validateRule } from "../../api/rules";
import type { RuleValidateResponse } from "../../types/api";

type Props = {
  expression: string;
  onChange: (value: string) => void;
  availableNames: string[];
};

export default function RuleEditor({ expression, onChange, availableNames }: Props) {
  const [result, setResult] = useState<RuleValidateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validating, setValidating] = useState(false);

  async function handleValidate() {
    setValidating(true);
    setError(null);
    setResult(null);

    try {
      const res = await validateRule({
        expression,
        available_names: availableNames,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rule validation failed");
    } finally {
      setValidating(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <textarea
        value={expression}
        onChange={(e) => onChange(e.target.value)}
        rows={5}
        style={{
          width: "100%",
          padding: 10,
          fontFamily: "monospace",
          fontSize: 14,
          boxSizing: "border-box",
        }}
        placeholder="Example: AwayTeamPPI > HomeTeamPPI and 0 < PPIDiff < 0.1"
      />

      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={handleValidate} disabled={validating || !expression.trim()}>
          {validating ? "Validating..." : "Validate rule"}
        </button>
      </div>

      {error && <div style={{ color: "#b00020" }}>{error}</div>}

      {result && (
        <div style={{ borderTop: "1px solid #eee", paddingTop: 12, display: "grid", gap: 6 }}>
          <div style={{ color: "green" }}>Rule is valid.</div>
          <div>
            <strong>Used names:</strong> {result.used_names.join(", ") || "-"}
          </div>
          <div>
            <strong>Unknown names:</strong> {result.unknown_names.join(", ") || "-"}
          </div>
        </div>
      )}

      <div>
        <strong>Available names</strong>
        <div
          style={{
            marginTop: 8,
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
          }}
        >
          {availableNames.map((name) => (
            <span
              key={name}
              style={{
                border: "1px solid #ddd",
                borderRadius: 999,
                padding: "4px 8px",
                fontSize: 12,
                background: "#fafafa",
              }}
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}