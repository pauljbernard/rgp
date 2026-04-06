import { compareDomainPack, getDomainPack, listDomainPackLineage, validateDomainPack } from "@/lib/server-api";
import { DataTable, PageShell, SectionHeading, Tabs, appShellProps, formatDate } from "../../../../components/ui-helpers";

import { activateDomainPackAction, installDomainPackAction } from "../actions";

export default async function AdminDomainPackDetailPage({
  params,
}: {
  params: Promise<{ packId: string }>;
}) {
  const { packId } = await params;
  const [detail, validationErrors, comparison, lineage] = await Promise.all([getDomainPack(packId), validateDomainPack(packId), compareDomainPack(packId), listDomainPackLineage(packId)]);
  const { pack, installations } = detail;

  return (
    <PageShell
      {...appShellProps("/admin/domain-packs", pack.name, "Inspect domain pack contributions, activation state, and tenant installations.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Pack State" />
          <div className="space-y-2 text-sm text-slate-700">
            <div>Status: {pack.status}</div>
            <div>Version: {pack.version}</div>
            <div>Activated: {pack.activated_at ? formatDate(pack.activated_at) : "—"}</div>
          </div>
          <form action={activateDomainPackAction}>
            <input type="hidden" name="packId" value={pack.id} />
            <button type="submit" className="w-full rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
              Activate Pack
            </button>
          </form>
          <form action={installDomainPackAction}>
            <input type="hidden" name="packId" value={pack.id} />
            <button type="submit" className="w-full rounded-md border border-chrome bg-white px-4 py-2 text-sm font-medium text-slate-700">
              Install Pack
            </button>
          </form>
        </div>
      }
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
          <h2 className="text-lg font-semibold">Description</h2>
          <p className="mt-2 text-sm text-slate-700">{pack.description || "No description provided."}</p>
        </div>
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Validation</h2>
          {validationErrors.length ? (
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-rose-700">
              {validationErrors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-emerald-700">Pack contributions satisfy the current governance checks.</p>
          )}
        </div>
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Version Comparison</h2>
          <p className="mt-2 text-sm text-slate-700">{comparison.summary}</p>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-chrome bg-white px-4 py-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Current Version</div>
              <div className="mt-1 text-sm font-medium text-slate-900">{comparison.current_version}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-4 py-3">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Baseline Version</div>
              <div className="mt-1 text-sm font-medium text-slate-900">{comparison.baseline_version ?? "No prior version"}</div>
            </div>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {comparison.deltas.map((delta) => (
              <div key={delta.category} className="rounded-lg border border-chrome bg-white px-4 py-3">
                <h3 className="text-sm font-semibold text-slate-900">{delta.category.replace("_", " ")}</h3>
                <p className="mt-2 text-xs font-medium uppercase tracking-wide text-emerald-700">Added</p>
                <p className="mt-1 text-sm text-slate-700">{delta.added.join(", ") || "—"}</p>
                <p className="mt-3 text-xs font-medium uppercase tracking-wide text-rose-700">Removed</p>
                <p className="mt-1 text-sm text-slate-700">{delta.removed.join(", ") || "—"}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Version Lineage</h2>
          <DataTable
            data={lineage}
            emptyMessage="No related pack lineage recorded."
            columns={[
              { key: "version", header: "Version", render: (row) => row.version },
              { key: "status", header: "Status", render: (row) => row.status },
              { key: "contributions", header: "Contributions", render: (row) => String(row.contribution_count) },
              { key: "created", header: "Created", render: (row) => (row.created_at ? formatDate(row.created_at) : "—") },
              { key: "activated", header: "Activated", render: (row) => (row.activated_at ? formatDate(row.activated_at) : "—") },
              { key: "pack", header: "Pack ID", render: (row) => row.pack_id },
            ]}
          />
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <h3 className="text-sm font-semibold text-slate-900">Contributed Templates</h3>
            <p className="mt-2 text-sm text-slate-700">{pack.contributed_templates.join(", ") || "—"}</p>
          </div>
          <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <h3 className="text-sm font-semibold text-slate-900">Contributed Workflows</h3>
            <p className="mt-2 text-sm text-slate-700">{pack.contributed_workflows.join(", ") || "—"}</p>
          </div>
          <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <h3 className="text-sm font-semibold text-slate-900">Artifact Types</h3>
            <p className="mt-2 text-sm text-slate-700">{pack.contributed_artifact_types.join(", ") || "—"}</p>
          </div>
          <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <h3 className="text-sm font-semibold text-slate-900">Policies</h3>
            <p className="mt-2 text-sm text-slate-700">{pack.contributed_policies.join(", ") || "—"}</p>
          </div>
        </div>
        <DataTable
          data={installations}
          emptyMessage="No installations recorded."
          columns={[
            { key: "id", header: "Installation", render: (row) => row.id },
            { key: "version", header: "Version", render: (row) => row.installed_version },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "installed_by", header: "Installed By", render: (row) => row.installed_by },
            { key: "installed_at", header: "Installed At", render: (row) => (row.installed_at ? formatDate(row.installed_at) : "—") },
          ]}
        />
      </div>
    </PageShell>
  );
}
