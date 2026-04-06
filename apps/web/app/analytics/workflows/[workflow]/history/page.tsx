import { getWorkflowHistory } from "@/lib/server-api";
import Link from "next/link";
import { DataTable, FilterPanel, PageShell, appShellProps } from "../../../../../components/ui-helpers";

function decodeWorkflow(value: string) {
  return decodeURIComponent(value);
}

export default async function WorkflowHistoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ workflow: string }>;
  searchParams?: Promise<{ event_class?: string; source_system?: string }>;
}) {
  const { workflow: encodedWorkflow } = await params;
  const workflow = decodeWorkflow(encodedWorkflow);
  const filters = (await searchParams) ?? {};
  const history = await getWorkflowHistory(workflow, 200);
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
    return query
      ? `/analytics/workflows/${encodeURIComponent(workflow)}/history?${query}`
      : `/analytics/workflows/${encodeURIComponent(workflow)}/history`;
  };

  return (
    <PageShell
      {...appShellProps(
        "/analytics/workflows",
        `${workflow} History`,
        "Workflow-scoped unified timeline across canonical governance, execution snapshots, and federated projection activity."
      )}
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/analytics/workflows" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
            Back to Workflows
          </Link>
          <Link href={`/analytics/workflows/${encodeURIComponent(workflow)}/federation`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
            Open Federation View
          </Link>
        </div>
        <FilterPanel
          items={[
            { label: "Workflow", value: workflow },
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
              <Link href={withFilters({ event_class: "federated_resolution" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Resolutions
              </Link>
            </>
          }
        />
        <DataTable
          data={filteredHistory}
          emptyMessage="No workflow history available."
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
            {
              key: "related",
              header: "Related Entity",
              render: (row) =>
                row.related_entity_type && row.related_entity_id
                  ? `${row.related_entity_type}:${row.related_entity_id}`
                  : "—"
            },
            { key: "lineage", header: "Lineage", render: (row) => (row.lineage.length ? row.lineage.join(" -> ") : "—") },
            { key: "reason", header: "Reason / Evidence", render: (row) => row.reason_or_evidence }
          ]}
        />
      </div>
    </PageShell>
  );
}
