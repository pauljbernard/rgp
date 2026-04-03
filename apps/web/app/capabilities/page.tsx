import { listCapabilities } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, PageShell, appShellProps, formatDate, statusTone } from "../../components/ui-helpers";

export default async function CapabilitiesPage() {
  const data = await listCapabilities();

  return (
    <PageShell {...appShellProps("/capabilities", "Capability Registry", "Browse active, pending, and deprecated capabilities under governance.")}>
      <div className="space-y-4">
        <FilterPanel
          items={[
            { label: "Type", value: "All" },
            { label: "Status", value: "All" },
            { label: "Owner", value: "All teams" }
          ]}
        />
        <DataTable
          data={data.items}
          emptyMessage="No capabilities registered."
          columns={[
            { key: "name", header: "Name", render: (row) => <Link href={`/capabilities/${row.id}`} className="text-accent">{row.name}</Link> },
            { key: "type", header: "Type", render: (row) => row.type },
            { key: "version", header: "Version", render: (row) => row.version },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "owner", header: "Owner", render: (row) => row.owner },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) },
            { key: "usage", header: "Usage Count", render: (row) => row.usage_count }
          ]}
        />
      </div>
    </PageShell>
  );
}
