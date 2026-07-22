/**
 * API client for the Coalesce Ops Console backend.
 *
 * The Run type mirrors the backend's pydantic Run model. Keep them in sync.
 */

export interface Run {
  id: string;
  name: string;
  status: string;
  environment: string;
  started_at: string | null;
  duration_seconds: number | null;
}

/**
 * Fetch recent runs from the backend. Vite proxies /api to the FastAPI service.
 */
export async function fetchRuns(): Promise<Run[]> {
  const response = await fetch("/api/runs");
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }
  return (await response.json()) as Run[];
}
