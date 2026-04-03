import { listArtifacts } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, PageShell, appShellProps, formatDate, statusTone } from "../../components/ui-helpers";

export default async function ArtifactsPage() {
  const data = await listArtifacts();

  return (
    <PageShell {...appShellProps("/artifacts", "Artifacts", "Browse governed outputs, versions, and review readiness across the platform.")}>
      <div className="space-y-4">
        <FilterPanel
          items={[
            { label: "Type", value: "All" },
            { label: "Status", value: "All" },
            { label: "Review State", value: "All" },
            { label: "Promotion Relevant", value: "Any" }
          ]}
        />
        <DataTable
          data={data.items}
          emptyMessage="No artifacts found."
          columns={[
            { key: "id", header: "Artifact ID", render: (row) => <Link href={`/artifacts/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            { key: "type", header: "Type", render: (row) => row.type },
            { key: "name", header: "Name", render: (row) => row.name },
            { key: "version", header: "Current Version", render: (row) => row.current_version },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "request", header: "Request ID", render: (row) => <Link href={`/requests/${row.request_id}`} className="text-accent">{row.request_id}</Link> },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) },
            { key: "owner", header: "Owner", render: (row) => row.owner }
          ]}
        />
      </div>
    </PageShell>
  );
}
