import { listAdminOrganizations, listAdminTeams, listAdminTenants, listAdminUsers } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../../components/ui-helpers";
import { updateTenantAction } from "../../actions";

export default async function TenantDetailPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = await params;
  const [tenants, organizations, teams, users] = await Promise.all([
    listAdminTenants(),
    listAdminOrganizations(),
    listAdminTeams(),
    listAdminUsers(),
  ]);
  const tenant = tenants.find((row) => row.id === tenantId);
  if (!tenant) {
    return (
      <PageShell {...appShellProps("/admin/org", "Tenant Not Found", "The requested tenant could not be found.")}>
        <div className="rounded-xl border border-chrome bg-white p-6 text-sm text-slate-600 shadow-sm">Tenant not found.</div>
      </PageShell>
    );
  }
  const tenantOrganizations = organizations.filter((organization) => organization.tenant_id === tenant.id);
  const tenantTeams = teams.filter((team) => team.tenant_id === tenant.id);
  const tenantUsers = users.filter((user) => user.tenant_id === tenant.id);

  return (
    <PageShell
      {...appShellProps("/admin/org", tenant.name, "Platform-admin tenant detail and maintenance page.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Tenant Summary" />
          <div className="space-y-2 text-sm text-slate-700">
            <div><span className="font-medium text-slate-900">{tenant.name}</span></div>
            <div className="font-mono text-xs text-slate-500">{tenant.id}</div>
            <div>Status: {tenant.status}</div>
            <div>Organizations: {tenantOrganizations.length}</div>
            <div>Teams: {tenantTeams.length}</div>
            <div>Users: {tenantUsers.length}</div>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="org"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" }
          ]}
        />
        <section className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Edit Tenant" />
          <form action={updateTenantAction} className="mt-4 grid gap-3 md:grid-cols-2">
            <input type="hidden" name="tenantId" value={tenant.id} />
            <label className="space-y-1 text-sm text-slate-700">
              <span className="block text-xs font-medium text-slate-500">Name</span>
              <input name="name" defaultValue={tenant.name} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
            </label>
            <label className="space-y-1 text-sm text-slate-700">
              <span className="block text-xs font-medium text-slate-500">Status</span>
              <select name="status" defaultValue={tenant.status} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <option value="active">active</option>
                <option value="pending">pending</option>
                <option value="disabled">disabled</option>
              </select>
            </label>
            <div className="md:col-span-2 flex justify-end">
              <Button label="Save Tenant" tone="primary" type="submit" />
            </div>
          </form>
        </section>
      </div>
    </PageShell>
  );
}
