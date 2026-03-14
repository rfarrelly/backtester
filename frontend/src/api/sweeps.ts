import { apiFetch } from "./client";
import type { DatasetSweepRequest, DatasetSweepResponse } from "../types/api";

export async function runDatasetSweep(
  datasetId: string,
  body: DatasetSweepRequest
): Promise<DatasetSweepResponse> {
  return apiFetch<DatasetSweepResponse>(`/datasets/${datasetId}/sweeps`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}