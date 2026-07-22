import { useQuery } from "@tanstack/react-query";
import { fetchRuns } from "./api";
import { RunsTable } from "./components/RunsTable";

/**
 * The whole app: fetch runs, show status, let the user refresh.
 */
export default function App() {
  const { data, isLoading, isError, error, refetch, isFetching, dataUpdatedAt } =
    useQuery({ queryKey: ["runs"], queryFn: fetchRuns });

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : "-";

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Coalesce Ops Console
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Recent job runs. Last updated {lastUpdated}.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="rounded-md border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-slate-700 disabled:opacity-50"
        >
          {isFetching ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {isLoading && <p className="text-slate-400">Loading runs...</p>}

      {isError && (
        <div className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
          Could not load runs: {(error as Error).message}. Is the backend running
          on port 8000?
        </div>
      )}

      {data && <RunsTable runs={data} />}
    </div>
  );
}
