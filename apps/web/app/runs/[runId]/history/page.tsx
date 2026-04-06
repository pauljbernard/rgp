import { getRunHistory } from "@/lib/server-api";
import Link from "next/link";
import { DataTable, FilterPanel, PageShell, appShellProps } from "../../../../components/ui-helpers";

export default async function RunHistoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ runId: string }>;
  searchParams?: Promise<{ event_class?: string; source_system?: string }>;
}) {
  const { runId } = await params;
  const filters = (await searchParams) ?? {};
  const history = await getRunHistory(runId);
  const filteredHistory = history.filter((entry) => {
    if (filters.event_class && entry.event_class !== filters.event_class) {
      return false;
    }
    if (filters.source_system && (entry.source_system ?? "RGP") !== filters.source_system) {
      return false;
    }
    return true;
  });
  const withFilters = (overrides: Record<string, string | undefined>) => {
    const next = new URLSearchParams();
    for (const [key, value] of Object.entries({ ...filters, ...overrides })) {
      if (value) {
        next.set(key, value);
      }
    }
    const query = next.toString();
    return query ? `/runs/${runId}/history?${query}` : `/runs/${runId}/history`;
  };

  return (
    <PageShell
      {...appShellProps(
        "/runs",
        "Run History",
        "Unified run timeline including canonical execution activity and request-linked federated history."
      )}
    >
      <FilterPanel
        items={[
          { label: "Event Class", value: filters.event_class ?? "All events", active: Boolean(filters.event_class) },
          { label: "Source", value: filters.source_system ?? "All systems", active: Boolean(filters.source_system) }
        ]}
        actions={
          <>
            <Link href={withFilters({ event_class: undefined, source_system: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
              Clear
            </Link>
            <Link href={withFilters({ event_class: "canonical" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
              Canonical Only
            </Link>
            <Link href={withFilters({ event_class: "federated_sync" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
              Federated Sync
            </Link>
          </>
        }
      />
      <DataTable
        data={filteredHistory}
        emptyMessage="No run history available."
        columns={[
          { key: "timestamp", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
          {
            key: "event_class",
            header: "Event Class",
            render: (row) => (
              <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                {row.event_class.replaceAll("_", " ")}
              </span>
            )
          },
          { key: "actor", header: "Actor", render: (row) => row.actor },
          { key: "action", header: "Action", render: (row) => row.action },
          { key: "source", header: "Source", render: (row) => row.source_system ?? "RGP" },
          { key: "type", header: "Object Type", render: (row) => row.object_type },
          { key: "id", header: "Object ID", render: (row) => row.object_id },
          { key: "lineage", header: "Lineage", render: (row) => (row.lineage.length ? row.lineage.join(" -> ") : "—") },
          { key: "reason", header: "Reason / Evidence", render: (row) => row.reason_or_evidence }
        ]}
      />
    </PageShell>
  );
}
