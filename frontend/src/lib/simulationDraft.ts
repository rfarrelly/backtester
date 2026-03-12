import type { DatasetMapping, SimulationRequest } from "../types/api";

export type SimulationDraft = {
  sourceRunId?: string | null;
  mapping: DatasetMapping;
  request: SimulationRequest;
  savedAt: string;
};

function storageKey(datasetId: string): string {
  return `simDraft:${datasetId}`;
}

export function saveSimulationDraft(
  datasetId: string,
  draft: Omit<SimulationDraft, "savedAt">
): void {
  const payload: SimulationDraft = {
    ...draft,
    savedAt: new Date().toISOString(),
  };

  localStorage.setItem(storageKey(datasetId), JSON.stringify(payload));
}

export function loadSimulationDraft(datasetId: string): SimulationDraft | null {
  const raw = localStorage.getItem(storageKey(datasetId));
  if (!raw) return null;

  try {
    return JSON.parse(raw) as SimulationDraft;
  } catch {
    return null;
  }
}

export function clearSimulationDraft(datasetId: string): void {
  localStorage.removeItem(storageKey(datasetId));
}