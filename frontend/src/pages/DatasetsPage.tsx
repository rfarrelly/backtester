import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteDataset, listDatasets, uploadDataset } from "../api/datasets";
import type { DatasetSummary } from "../types/api";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const data = await listDatasets();
      setDatasets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleFileChange(file: File | null) {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      await uploadDataset(file);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload dataset");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(datasetId: string) {
    const confirmed = window.confirm("Delete this dataset?");
    if (!confirmed) return;

    try {
      await deleteDataset(datasetId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete dataset");
    }
  }

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <section style={{ display: "grid", gap: 12 }}>
        <h2 style={{ margin: 0 }}>Datasets</h2>
        <div
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 16,
            display: "grid",
            gap: 8,
          }}
        >
          <label style={{ display: "grid", gap: 8 }}>
            <span>Upload CSV dataset</span>
            <input
              type="file"
              accept=".csv"
              disabled={uploading}
              onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            />
          </label>
          {uploading && <div>Uploading...</div>}
        </div>
      </section>

      {error && (
        <div style={{ color: "#b00020" }}>
          {error}
        </div>
      )}

      <section style={{ display: "grid", gap: 12 }}>
        <h3 style={{ margin: 0 }}>Your datasets</h3>

        {loading ? (
          <div>Loading datasets...</div>
        ) : datasets.length === 0 ? (
          <div>No datasets uploaded yet.</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={thStyle}>Filename</th>
                <th style={thStyle}>Created</th>
                <th style={thStyle}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.dataset_id}>
                  <td style={tdStyle}>{dataset.filename}</td>
                  <td style={tdStyle}>{dataset.created_at ?? "-"}</td>
                  <td style={tdStyle}>
                    <div style={{ display: "flex", gap: 8 }}>
                      <Link to={`/datasets/${dataset.dataset_id}`}>Open</Link>
                      <button
                        onClick={() => handleDelete(dataset.dataset_id)}
                        style={{ cursor: "pointer" }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  textAlign: "left",
  borderBottom: "1px solid #ddd",
  padding: "8px 12px",
};

const tdStyle: React.CSSProperties = {
  borderBottom: "1px solid #eee",
  padding: "8px 12px",
};