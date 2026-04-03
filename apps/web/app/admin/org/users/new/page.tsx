import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../../components/ui-helpers";
import { createUserAction } from "../../actions";

export default function AdminNewUserPage() {
  return (
    <PageShell
      {...appShellProps("/admin/org", "Create User", "Create a user record, then add that user to teams from team management pages.")}
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
          <SectionHeading title="Create User" />
          <form action={createUserAction} className="mt-3 space-y-4">
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">User Id</span><input name="id" placeholder="user_analyst" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Display Name</span><input name="displayName" placeholder="Delivery Analyst" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Email</span><input name="email" placeholder="analyst@example.com" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Roles</span><input name="roles" placeholder="admin, reviewer" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <div className="flex justify-end"><Button label="Create User" tone="primary" type="submit" /></div>
          </form>
        </div>
      </div>
    </PageShell>
  );
}
