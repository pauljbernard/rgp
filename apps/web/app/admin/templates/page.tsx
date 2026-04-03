import React from "react";
import { listAdminTemplates } from "@/lib/server-api";
import { DataTable, PageShell, SectionHeading, Tabs, appShellProps } from "../../../components/ui-helpers";

export default async function AdminTemplatesPage() {
  const templates = await listAdminTemplates();

  return (
    <PageShell
      {...appShellProps("/admin/templates", "Admin Templates", "Catalog-first template registry. Open a version to author or review it in a dedicated drill-down surface.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <SectionHeading title="Catalog Summary" />
            <p className="mt-2 text-sm text-slate-600">
              The main panel is the system of record for template versions. Open a specific version to author, validate, compare, publish, or deprecate it.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Published</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{templates.filter((template) => template.status === "published").length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Draft</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{templates.filter((template) => template.status === "draft").length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Deprecated</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{templates.filter((template) => template.status === "deprecated").length}</div>
            </div>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="templates"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" },
          ]}
        />
        <DataTable
          data={templates}
          emptyMessage="No templates available."
          columns={[
            {
              key: "name",
              header: "Template",
              render: (row) => (
                <a href={`/admin/templates/${encodeURIComponent(row.id)}/${encodeURIComponent(row.version)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">
                  {row.name}
                </a>
              ),
            },
            { key: "id", header: "Template Id", render: (row) => <span className="font-mono text-xs text-slate-600">{row.id}</span> },
            { key: "version", header: "Version", render: (row) => row.version },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "updated_at", header: "Updated", render: (row) => new Date(row.updated_at).toLocaleString() },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <a href={`/admin/templates/${encodeURIComponent(row.id)}/${encodeURIComponent(row.version)}`} className="rounded-lg border border-chrome px-3 py-2 text-xs font-medium text-slate-700">
                  Open Version
                </a>
              ),
            },
          ]}
        />
      </div>
    </PageShell>
  );
}
