import { listKnowledge } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, PageShell, appShellProps, formatDate, statusTone } from "../../components/ui-helpers";

export default async function KnowledgePage({
  searchParams,
}: {
  searchParams?: Promise<{ query?: string; status?: string }>;
}) {
  const filters = (await searchParams) ?? {};
  const data = await listKnowledge({ page_size: 25, query: filters.query, status: filters.status });

  return (
    <PageShell {...appShellProps("/knowledge", "Knowledge", "Browse governed knowledge artifacts, publication state, and reusable context assets.")}>
      <div className="space-y-4">
        <FilterPanel
          items={[
            { label: "Search", value: filters.query ?? "All" },
            { label: "Status", value: filters.status ?? "All" },
            { label: "Artifacts", value: String(data.total_count) }
          ]}
          actions={
            <>
              <form action="/knowledge" className="flex flex-wrap items-end gap-2">
                <div className="grid gap-1">
                  <label htmlFor="knowledge-query" className="text-xs font-medium text-slate-600">Search</label>
                  <input id="knowledge-query" name="query" defaultValue={filters.query ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
                </div>
                <div className="grid gap-1">
                  <label htmlFor="knowledge-status" className="text-xs font-medium text-slate-600">Status</label>
                  <select id="knowledge-status" name="status" defaultValue={filters.status ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                    <option value="">All</option>
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                    <option value="deprecated">Deprecated</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
                <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">Apply</button>
              </form>
              <Link href="/knowledge/new" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
                New Knowledge Artifact
              </Link>
            </>
          }
        />
        <DataTable
          data={data.items}
          emptyMessage="No knowledge artifacts found."
          columns={[
            { key: "id", header: "Artifact ID", render: (row) => <Link href={`/knowledge/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            { key: "name", header: "Name", render: (row) => <Link href={`/knowledge/${row.id}`} className="font-medium text-slate-900 hover:text-accent hover:underline">{row.name}</Link> },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "version", header: "Version", render: (row) => `v${row.version}` },
            { key: "type", header: "Content Type", render: (row) => row.content_type },
            { key: "tags", header: "Tags", render: (row) => row.tags.join(", ") || "—" },
            { key: "updated", header: "Updated", render: (row) => (row.updated_at ? formatDate(row.updated_at) : "—") },
          ]}
        />
      </div>
    </PageShell>
  );
}
