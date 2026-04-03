import { listAdminPortfolios, listAdminTeams, listAdminUsers } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../../components/ui-helpers";
import { addTeamMembershipAction, createUserAndAddTeamMembershipAction, updateTeamAction } from "../../actions";

type TeamDetailPageProps = {
  params: Promise<{ teamId: string }>;
};

export default async function AdminTeamDetailPage({ params }: TeamDetailPageProps) {
  const { teamId } = await params;
  const [users, teams, portfolios] = await Promise.all([listAdminUsers(), listAdminTeams(), listAdminPortfolios()]);
  const team = teams.find((item) => item.id === teamId) ?? teams[0];

  if (!team) {
    return (
      <PageShell
        {...appShellProps("/admin/org", "Team Detail", "The requested team was not found.")}
        contextPanel={<a href="/admin/org" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Organization</a>}
      >
        <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm text-sm text-slate-600">No team available.</div>
      </PageShell>
    );
  }

  const availableUsers = users.filter((user) => !team.members.some((member) => member.user_id === user.id));
  const relatedPortfolios = portfolios.filter((portfolio) => portfolio.owner_team_id === team.id || portfolio.scope_keys.includes(team.id));

  return (
    <PageShell
      {...appShellProps("/admin/org", `Team: ${team.name}`, "Edit team settings and manage users in the context of one team.")}
      contextPanel={
        <div className="space-y-5">
          <a href="/admin/org" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Organization</a>
          <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
            <SectionHeading title="Selected Team" />
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              <div><span className="font-medium text-slate-900">{team.name}</span></div>
              <div className="font-mono text-xs text-slate-500">{team.id}</div>
              <div>Kind: {team.kind}</div>
              <div>Status: {team.status}</div>
              <div>Members: {team.member_count}</div>
            </div>
          </div>

          <form action={addTeamMembershipAction} className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
            <div className="mb-3 text-sm font-semibold text-slate-800">Add Existing User</div>
            <input type="hidden" name="teamId" value={team.id} />
            <div className="space-y-3">
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">User</span>
                <select name="userId" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
                  {availableUsers.map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>)}
                </select>
              </label>
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Team Role</span>
                <input name="role" defaultValue="member" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
            </div>
            <div className="mt-3 flex justify-end">
              <Button label="Add Membership" tone="primary" type="submit" />
            </div>
          </form>

          <form action={createUserAndAddTeamMembershipAction} className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
            <div className="mb-3 text-sm font-semibold text-slate-800">Create User In Team</div>
            <input type="hidden" name="teamId" value={team.id} />
            <div className="space-y-3">
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">User Id</span>
                <input name="id" placeholder="user_team_member" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Display Name</span>
                <input name="displayName" placeholder="Team Member" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Email</span>
                <input name="email" placeholder="member@example.com" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Global Roles</span>
                <input name="roles" placeholder="observer" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Team Role</span>
                <input name="membershipRole" defaultValue="member" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
            </div>
            <div className="mt-3 flex justify-end">
              <Button label="Create User and Add to Team" tone="primary" type="submit" />
            </div>
          </form>
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

        <section className="rounded-xl border border-chrome bg-white p-4 shadow-sm space-y-3">
          <SectionHeading title="Team Settings" />
          <form action={updateTeamAction} className="space-y-4">
            <input type="hidden" name="teamId" value={team.id} />
            <div className="grid gap-3 md:grid-cols-2">
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Team Name</span>
                <input name="name" defaultValue={team.name} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
              <label className="space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Kind</span>
                <input name="kind" defaultValue={team.kind} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
              <label className="space-y-1 text-sm text-slate-700 md:col-span-2">
                <span className="block text-xs font-medium text-slate-500">Status</span>
                <input name="status" defaultValue={team.status} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
              </label>
            </div>
            <div className="flex justify-end">
              <Button label="Save Team" tone="primary" type="submit" />
            </div>
          </form>
        </section>

        <section className="rounded-xl border border-chrome bg-white p-4 shadow-sm space-y-3">
          <SectionHeading title="Members" />
          <div className="overflow-hidden rounded-lg border border-chrome">
            <div className="grid grid-cols-[minmax(0,1.2fr)_220px_140px_220px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              <div>User</div>
              <div>Email</div>
              <div>Team Role</div>
              <div>Membership Editor</div>
            </div>
            <div className="divide-y divide-chrome">
              {team.members.map((member) => (
                <div key={member.user_id} className="grid grid-cols-[minmax(0,1.2fr)_220px_140px_220px] items-center px-4 py-3 text-sm text-slate-700">
                  <div>
                    <div className="font-medium text-slate-900">{member.display_name}</div>
                    <div className="mt-1 font-mono text-xs text-slate-500">{member.user_id}</div>
                  </div>
                  <div>{member.email}</div>
                  <div>{member.role}</div>
                  <form action={addTeamMembershipAction} className="flex items-center gap-2">
                    <input type="hidden" name="teamId" value={team.id} />
                    <input type="hidden" name="userId" value={member.user_id} />
                    <input name="role" defaultValue={member.role} className="w-28 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700" />
                    <Button label="Update Role" tone="secondary" type="submit" />
                  </form>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-chrome bg-white p-4 shadow-sm space-y-3">
          <SectionHeading title="Related Portfolios" />
          <div className="space-y-2">
            {relatedPortfolios.length ? (
              relatedPortfolios.map((portfolio) => (
                <div key={portfolio.id} className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                  <div className="font-medium text-slate-900">{portfolio.name}</div>
                  <div className="mt-1 font-mono text-xs text-slate-500">{portfolio.id}</div>
                  <div className="mt-2 text-sm">Owner: {portfolio.owner_team_id}</div>
                  <div className="mt-1 text-sm">Scope Teams: {portfolio.scope_keys.join(", ") || "none"}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-500">No related portfolios.</div>
            )}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
