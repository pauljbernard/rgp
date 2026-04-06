import { listDomainPacks } from "@/lib/server-api";
import { DataTable, PageShell, Tabs, appShellProps } from "../../../components/ui-helpers";

import { createDomainPackAction } from "./actions";

export default async function AdminDomainPacksPage() {
  const packs = await listDomainPacks();

  return (
    <PageShell
      {...appShellProps("/admin/domain-packs", "Admin Domain Packs", "Govern domain capability packs, contributions, activation state, and tenant installation readiness.")}
    >
      <div className="space-y-4">
        <Tabs
          activeKey="domain-packs"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "domain-packs", label: "Domain Packs", href: "/admin/domain-packs" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" },
          ]}
        />
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <form action={createDomainPackAction} className="grid gap-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <label htmlFor="domain-pack-name" className="text-sm font-medium text-slate-700">Name</label>
                <input id="domain-pack-name" name="name" required className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              </div>
              <div className="grid gap-2">
                <label htmlFor="domain-pack-version" className="text-sm font-medium text-slate-700">Version</label>
                <input id="domain-pack-version" name="version" required placeholder="1.0.0" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="grid gap-2">
              <label htmlFor="domain-pack-description" className="text-sm font-medium text-slate-700">Description</label>
              <textarea id="domain-pack-description" name="description" rows={3} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <input name="contributedTemplates" placeholder="tmpl_assessment, tmpl_editorial" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="contributedArtifactTypes" placeholder="document, media" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="contributedWorkflows" placeholder="wf_assessment_revision_v1" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="contributedPolicies" placeholder="pol_editorial_review" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="flex justify-end">
              <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
                Create Domain Pack
              </button>
            </div>
          </form>
        </div>
        <DataTable
          data={packs}
          emptyMessage="No domain packs registered."
          columns={[
            {
              key: "name",
              header: "Pack",
              render: (row) => (
                <a href={`/admin/domain-packs/${encodeURIComponent(row.id)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">
                  {row.name}
                </a>
              ),
            },
            { key: "version", header: "Version", render: (row) => row.version },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "templates", header: "Templates", render: (row) => String(row.contributed_templates.length) },
            { key: "workflows", header: "Workflows", render: (row) => String(row.contributed_workflows.length) },
          ]}
        />
      </div>
    </PageShell>
  );
}
