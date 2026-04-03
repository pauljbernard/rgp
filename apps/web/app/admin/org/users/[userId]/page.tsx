import { listAdminTeams, listAdminUsers } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../../components/ui-helpers";
import { updateUserAction } from "../../actions";

type UserDetailPageProps = {
  params: Promise<{ userId: string }>;
};

export default async function AdminUserDetailPage({ params }: UserDetailPageProps) {
  const { userId } = await params;
  const [users, teams] = await Promise.all([listAdminUsers(), listAdminTeams()]);
  const user = users.find((item) => item.id === userId) ?? users[0];

  if (!user) {
    return (
      <PageShell
        {...appShellProps("/admin/org", "User Detail", "The requested user was not found.")}
        contextPanel={<a href="/admin/org" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Organization</a>}
      >
        <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm text-sm text-slate-600">No user available.</div>
      </PageShell>
    );
  }

  const memberships = teams
    .filter((team) => team.members.some((member) => member.user_id === user.id))
    .map((team) => ({
      organizationName: team.organization_name,
      teamId: team.id,
      teamName: team.name,
      role: team.members.find((member) => member.user_id === user.id)?.role ?? "member",
    }));

  return (
    <PageShell
      {...appShellProps("/admin/org", `User: ${user.display_name}`, "Edit a user and inspect that user’s memberships across teams.")}
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
        <section className="rounded-xl border border-chrome bg-white p-4 shadow-sm space-y-3">
          <SectionHeading title="User Settings" />
          <form action={updateUserAction} className="space-y-4">
            <input type="hidden" name="userId" value={user.id} />
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Display Name</span><input name="displayName" defaultValue={user.display_name} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Email</span><input name="email" defaultValue={user.email} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Roles</span><input name="roles" defaultValue={user.role_summary.join(", ")} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700">
              <span className="block text-xs font-medium text-slate-500">Status</span>
              <select name="status" defaultValue={user.status} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <option value="pending_approval">pending_approval</option>
                <option value="pending_activation">pending_activation</option>
                <option value="active">active</option>
                <option value="suspended">suspended</option>
                <option value="disabled">disabled</option>
                <option value="rejected">rejected</option>
              </select>
            </label>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <div>Password configured: {user.has_password ? "yes" : "no"}</div>
              <div>Password reset required: {user.password_reset_required ? "yes" : "no"}</div>
              {user.registration_request_id ? <div>Provisioned from request: <span className="font-mono text-xs">{user.registration_request_id}</span></div> : null}
            </div>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Set Password</span><input type="password" name="password" placeholder={user.has_password ? "Enter a new password to rotate credentials" : "Set an initial password"} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" autoComplete="new-password" /></label>
            <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" name="requirePasswordReset" defaultChecked={user.password_reset_required} /> Require password reset before next sign-in</label>
            <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" name="resetPassword" /> Clear the current password and force administrator re-provisioning</label>
            <div className="flex justify-end"><Button label="Save User" tone="primary" type="submit" /></div>
          </form>
        </section>
        <section className="rounded-xl border border-chrome bg-white p-4 shadow-sm space-y-3">
          <SectionHeading title="Team Memberships" />
          <div className="space-y-2">
            {memberships.length ? memberships.map((membership) => (
              <a key={membership.teamId} href={`/admin/org/teams/${encodeURIComponent(membership.teamId)}`} className="block rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                <div className="font-medium text-slate-900">{membership.teamName}</div>
                <div className="mt-1 text-xs text-slate-500">Organization: {membership.organizationName}</div>
                <div className="mt-1 font-mono text-xs text-slate-500">{membership.teamId}</div>
                <div className="mt-2">Role: {membership.role}</div>
              </a>
            )) : <div className="text-sm text-slate-500">No team memberships.</div>}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
