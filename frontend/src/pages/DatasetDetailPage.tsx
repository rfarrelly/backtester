import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { introspectDataset } from "../api/datasets";
import type { DatasetIntrospection } from "../types/api";

export default function DatasetDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [data, setData] = useState<DatasetIntrospection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!datasetId) return;

      setLoading(true);
      setError(null);

      try {
        const result = await introspectDataset(datasetId);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dataset details");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [datasetId]);

  if (!datasetId) {
    return <div>Missing dataset id.</div>;
  }

  if (loading) {
    return <div>Loading dataset...</div>;
  }

  if (error) {
    return <div style={{ color: "#b00020" }}>{error}</div>;
  }

  if (!data) {
    return <div>No dataset data available.</div>;
  }

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <section>
        <h2 style={{ marginBottom: 8 }}>{data.filename}</h2>
        <div style={{ color: "#666" }}>Dataset ID: {data.dataset_id}</div>
      </section>

      <section style={{ display: "grid", gap: 12 }}>
        <h3 style={{ margin: 0 }}>Columns</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 8,
          }}
        >
          {data.columns.map((col) => (
            <div
              key={col}
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
      </section>

      <section style={{ display: "grid", gap: 12 }}>
        <h3 style={{ margin: 0 }}>Sample rows</h3>

        {data.sample_rows.length === 0 ? (
          <div>No sample rows available.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {data.columns.map((col) => (
                    <th key={col} style={thStyle}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.sample_rows.map((row, idx) => (
                  <tr key={idx}>
                    {data.columns.map((col) => (
                      <td key={col} style={tdStyle}>
                        {row[col] ?? ""}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section
        style={{
          border: "1px dashed #bbb",
          borderRadius: 8,
          padding: 16,
          background: "#fcfcfc",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Next step</h3>
        <p style={{ marginBottom: 0 }}>
          Next we will add the mapping form, rule validation, and simulation form to this page.
        </p>
      </section>
    </div>
  );
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
};