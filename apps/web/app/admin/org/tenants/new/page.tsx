import { PageShell, SectionHeading, Tabs, appShellProps, Button } from "../../../../../components/ui-helpers";
import { createTenantAction } from "../../actions";

export default function NewTenantPage() {
  return (
    <PageShell
      {...appShellProps("/admin/org", "Create Tenant", "Create a top-level tenant for a new organization space.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Tenant Guidance" />
          <p className="text-sm text-slate-600">
            Tenants are the top-level SaaS boundary. Organizations, teams, users, portfolios, templates, and policies can then be managed within each tenant.
          </p>
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
          <SectionHeading title="Create Tenant" />
          <form action={createTenantAction} className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="space-y-1 text-sm text-slate-700">
              <span className="block text-xs font-medium text-slate-500">Tenant Id</span>
              <input name="id" placeholder="tenant_new" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
            </label>
            <label className="space-y-1 text-sm text-slate-700">
              <span className="block text-xs font-medium text-slate-500">Name</span>
              <input name="name" placeholder="New Tenant" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
            </label>
            <label className="space-y-1 text-sm text-slate-700 md:col-span-2">
              <span className="block text-xs font-medium text-slate-500">Status</span>
              <select name="status" defaultValue="active" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <option value="active">active</option>
                <option value="pending">pending</option>
                <option value="disabled">disabled</option>
              </select>
            </label>
            <div className="md:col-span-2 flex justify-end">
              <Button label="Create Tenant" tone="primary" type="submit" />
            </div>
          </form>
        </section>
      </div>
    </PageShell>
  );
}
