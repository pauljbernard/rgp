import { PageShell } from "../../../components/ui-helpers";
import { HelpSection, HelpTabs, HelpTable, helpShellProps } from "../help-shared";

const adminAreas = [
  { area: "Templates", route: "/admin/templates", purpose: "Catalog-first template registry with version drill-down authoring." },
  { area: "Organization", route: "/admin/org", purpose: "Team-first organization catalog with membership and team drill-down management." },
  { area: "Integrations", route: "/admin/integrations", purpose: "Catalog-first integration registry for runtime and direct-assignment provider settings." },
  { area: "Policies", route: "/admin/policies", purpose: "Policy bundle and check-rule management." }
];

const adminForms = [
  { form: "Create Template / Draft Version", fields: "Template identity, version lineage, draft authoring fields, routing, governance requirements", outcome: "Creates or extends a template under governance." },
  { form: "Create User", fields: "User ID, display name, email, active status", outcome: "Creates a managed user record." },
  { form: "Create Team", fields: "Team ID, name, description, active status", outcome: "Creates a team that can own work and contain memberships." },
  { form: "Create Integration", fields: "Integration ID, name, type, provider, base URL, model, workspace, secret rotation fields", outcome: "Creates a managed integration that can later be edited in a drill-down page." },
  { form: "Policy Configuration", fields: "Policy metadata and rules", outcome: "Updates the policy catalog used by governance logic." }
];

export default function HelpAdminPage() {
  return (
    <PageShell
      {...helpShellProps("Help: Admin", "Guidance for template authoring, organization management, integration management, and policy administration.")}
      contextPanel={
        <div className="space-y-5 text-sm text-slate-600">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Admin Pattern</h2>
            <p className="mt-2">
              Admin surfaces are catalog-first. Start from the table view, then drill into a specific template version, team, user, or integration to edit it in context.
            </p>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpTabs activeKey="admin" />
        <HelpSection title="Admin Areas" description="These are the major authenticated administration sections and what they control.">
          <HelpTable
            data={adminAreas}
            columns={[
              { key: "area", header: "Area", render: (row) => row.area },
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "purpose", header: "Purpose", render: (row) => row.purpose }
            ]}
          />
        </HelpSection>
        <HelpSection title="Admin Forms and Fields" description="These are the major admin forms and the kinds of fields each one manages.">
          <HelpTable
            data={adminForms}
            columns={[
              { key: "form", header: "Form", render: (row) => row.form },
              { key: "fields", header: "Main Fields", render: (row) => row.fields },
              { key: "outcome", header: "Outcome", render: (row) => row.outcome }
            ]}
          />
        </HelpSection>
        <HelpSection title="Template Workbench" description="The template drill-down page is the authoritative authoring surface for request definitions.">
          <div className="grid gap-3 text-sm text-slate-700">
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use the template catalog to open one specific version.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Draft versions are editable. Published versions are immutable and require a successor draft for changes.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">The workbench supports field design, conditional rules, routing rules, governance requirements, preview, validation, comparison, publication, deprecation, and draft deletion.</div>
          </div>
        </HelpSection>
      </div>
    </PageShell>
  );
}
