import { getCapability } from "@/lib/server-api";
import { Badge, DataTable, EntityHeader, KeyValueGrid, PageShell, Tabs, appShellProps, statusTone } from "../../../components/ui-helpers";

export default async function CapabilityDetailPage({ params }: { params: Promise<{ capabilityId: string }> }) {
  const { capabilityId } = await params;
  const detail = await getCapability(capabilityId);

  return (
    <PageShell {...appShellProps("/capabilities", "Capability Detail", "Definition governance and lifecycle management for system capabilities.")}>
      <div className="space-y-4">
        <EntityHeader
          id={detail.capability.id}
          title={detail.capability.name}
          status={<Badge tone={statusTone(detail.capability.status)}>{detail.capability.status}</Badge>}
          ownership={detail.capability.owner}
        />
        <Tabs
          activeKey="overview"
          tabs={[
            { key: "overview", label: "Overview", href: `/capabilities/${detail.capability.id}` },
            { key: "definition", label: "Definition" },
            { key: "lineage", label: "Lineage" },
            { key: "usage", label: "Usage" },
            { key: "performance", label: "Performance" },
            { key: "history", label: "History" }
          ]}
        />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <KeyValueGrid items={detail.usage.map(([label, value]) => ({ label, value }))} />
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Definition</div>
              <div className="mt-2 text-sm text-slate-700">{detail.definition}</div>
            </div>
          </div>
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <div className="text-xs font-medium text-slate-500">Lineage</div>
            <div className="space-y-2">
              {detail.lineage.map((entry) => (
                <div key={entry} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm">{entry}</div>
              ))}
            </div>
          </div>
        </div>
        <DataTable
          data={detail.history}
          emptyMessage="No capability history."
          columns={[
            { key: "time", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
            { key: "actor", header: "Actor", render: (row) => row.actor },
            { key: "action", header: "Action", render: (row) => row.action }
          ]}
        />
      </div>
    </PageShell>
  );
}
