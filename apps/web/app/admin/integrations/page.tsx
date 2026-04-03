import { listIntegrations } from "@/lib/server-api";
import { DataTable, PageShell, SectionHeading, Tabs, appShellProps } from "../../../components/ui-helpers";

export default async function AdminIntegrationsPage() {
  const integrations = await listIntegrations();
  return (
    <PageShell
      {...appShellProps("/admin/integrations", "Admin Integrations", "Catalog-first integration registry. Open an integration to edit or delete it in a drill-down page.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <SectionHeading title="Management Pages" />
            <p className="mt-2 text-sm text-slate-600">
              The main panel is the integration catalog. Use the create page for new integrations and drill into existing integrations to edit or delete them.
            </p>
          </div>
          <a href="/admin/integrations/new" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">
            Create Integration
          </a>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="integrations"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" }
          ]}
        />
        <DataTable
          data={integrations}
          emptyMessage="No integrations configured."
          columns={[
            { key: "name", header: "Name", render: (row) => <a href={`/admin/integrations/${encodeURIComponent(row.id)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">{row.name}</a> },
            { key: "type", header: "Type", render: (row) => row.type },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "endpoint", header: "Configured Endpoint", render: (row) => row.endpoint },
            { key: "resolved", header: "Resolved Target", render: (row) => row.resolved_endpoint ?? "N/A" },
            { key: "actions", header: "Actions", render: (row) => <a href={`/admin/integrations/${encodeURIComponent(row.id)}`} className="rounded-lg border border-chrome px-3 py-2 text-xs font-medium text-slate-700">Open Integration</a> }
          ]}
        />
      </div>
    </PageShell>
  );
}
