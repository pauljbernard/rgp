import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../../components/ui-helpers";
import { createTeamAction } from "../../actions";

export default function AdminNewTeamPage() {
  return (
    <PageShell
      {...appShellProps("/admin/org", "Create Team", "Create a team, then manage members from the team detail page.")}
      contextPanel={<a href="/admin/org" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Organization</a>}
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
        <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Create Team" />
          <form action={createTeamAction} className="mt-3 space-y-4">
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Team Id</span><input name="id" placeholder="team_delivery_ops" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Name</span><input name="name" placeholder="Delivery Operations" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Kind</span><input name="kind" defaultValue="delivery" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <div className="flex justify-end"><Button label="Create Team" tone="primary" type="submit" /></div>
          </form>
        </div>
      </div>
    </PageShell>
  );
}
