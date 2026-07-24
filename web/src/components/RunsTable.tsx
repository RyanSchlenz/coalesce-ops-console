import type { Run } from "../api";

/**
 * Render a list of runs as a table with color-coded status.
 */
export function RunsTable({ runs }: { runs: Run[] }) {
  if (runs.length === 0) {
    return <p className="text-slate-400">No runs found.</p>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="px-4 py-3 font-medium">Run</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Environment</th>
            <th className="px-4 py-3 font-medium">Started</th>
            <th className="px-4 py-3 font-medium">Duration</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr
              key={run.id}
              className="border-t border-slate-800 hover:bg-slate-900/50"
            >
              <td className="px-4 py-3">
                <span className="font-medium text-slate-100">{run.name}</span>
                <span className="ml-2 text-xs text-slate-500">#{run.id}</span>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={run.status} />
              </td>
              <td className="px-4 py-3 text-slate-300">{run.environment}</td>
              <td className="px-4 py-3 text-slate-400">
                {formatStarted(run.started_at)}
              </td>
              <td className="px-4 py-3 text-slate-400">
                {formatDuration(run.duration_seconds)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * A colored pill for a run status. Unknown statuses fall back to gray.
 */
function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    success: "bg-green-900/50 text-green-300 border-green-800",
    completed: "bg-green-900/50 text-green-300 border-green-800",
    failed: "bg-red-900/50 text-red-300 border-red-800",
    error: "bg-red-900/50 text-red-300 border-red-800",
    running: "bg-blue-900/50 text-blue-300 border-blue-800",
    initializing: "bg-blue-900/50 text-blue-300 border-blue-800",
    rendering: "bg-blue-900/50 text-blue-300 border-blue-800",
    canceled: "bg-amber-900/40 text-amber-300 border-amber-800",
  };
  const style = styles[status] ?? "bg-slate-800 text-slate-300 border-slate-700";

  return (
    <span
      className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${style}`}
    >
      {status}
    </span>
  );
}

/**
 * Format an ISO timestamp as a readable local time, or a dash if missing.
 */
function formatStarted(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

/**
 * Format a duration in seconds as m s, or "in progress" if null.
 */
function formatDuration(seconds: number | null): string {
  if (seconds === null) return "in progress";
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}
