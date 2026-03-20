import { apiFetch } from "./client";
import type {
  DatasetIntrospection,
  DatasetSimulateRequest,
  DatasetSummary,
  SimulationResult,
} from "../../src/types/api";

export async function listDatasets(): Promise<DatasetSummary[]> {
  return apiFetch<DatasetSummary[]>("/datasets");
}

export async function uploadDataset(file: File): Promise<{ dataset_id: string; filename: string }> {
  const form = new FormData();
  form.append("file", file);

  return apiFetch<{ dataset_id: string; filename: string }>("/datasets/upload", {
    method: "POST",
    body: form,
  });
}

export async function introspectDataset(datasetId: string): Promise<DatasetIntrospection> {
  return apiFetch<DatasetIntrospection>(`/datasets/${datasetId}/introspect`);
}

export async function deleteDataset(datasetId: string): Promise<{ status: string; dataset_id: string }> {
  return apiFetch<{ status: string; dataset_id: string }>(`/datasets/${datasetId}`, {
    method: "DELETE",
  });
}

export async function simulateDataset(
  datasetId: string,
  payload: DatasetSimulateRequest
): Promise<SimulationResult> {
  return apiFetch<SimulationResult>(`/datasets/${datasetId}/simulate`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getDistinctValues(
  datasetId: string,
  column: string,
  limit = 500
): Promise<{ dataset_id: string; column: string; values: string[] }> {
  const params = new URLSearchParams({
    column,
    limit: String(limit),
  });

  return apiFetch<{ dataset_id: string; column: string; values: string[] }>(
    `/datasets/${datasetId}/distinct-values?${params.toString()}`
  );
}