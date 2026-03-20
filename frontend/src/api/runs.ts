import { apiFetch, getApiBaseUrl, getAccessToken } from "./client";
import type { RunDetail, RunSummary } from "../../src/types/api";

export async function listRuns(): Promise<RunSummary[]> {
  return apiFetch<RunSummary[]>("/runs");
}

export async function getRun(runId: string): Promise<RunDetail> {
  return apiFetch<RunDetail>(`/runs/${runId}`);
}

export async function deleteRun(runId: string): Promise<{ status: string; run_id: string }> {
  return apiFetch<{ status: string; run_id: string }>(`/runs/${runId}`, {
    method: "DELETE",
  });
}

export async function downloadRunBetsCsv(runId: string): Promise<void> {
  const token = getAccessToken();
  const response = await fetch(`${getApiBaseUrl()}/runs/${runId}/export/bets.csv`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`Failed to export CSV (HTTP ${response.status})`);
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `run_${runId}_bets.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
}