import { listAdminPortfolios, listAdminTeams, listAdminUsers } from "@/lib/server-api";
import { PageShell, SectionHeading, Tabs, appShellProps } from "../../../components/ui-helpers";

export default async function AdminOrgPage() {
  const [users, teams, portfolios] = await Promise.all([listAdminUsers(), listAdminTeams(), listAdminPortfolios()]);

  return (
    <PageShell
      {...appShellProps("/admin/org", "Admin Organization", "Team-first organization catalog with expandable membership hierarchy and team drill-down editing.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <SectionHeading title="Catalog Summary" />
            <p className="mt-2 text-sm text-slate-600">
              The main panel is a hierarchical team catalog. Expand a team to inspect memberships, and open a team to edit it and manage users in context.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Users</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{users.length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Teams</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{teams.length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Portfolios</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{portfolios.length}</div>
            </div>
          </div>

          <div className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
            <SectionHeading title="Management Pages" />
            <div className="flex flex-col gap-2 text-sm">
              <a href="/admin/org/users/new" className="rounded-lg border border-chrome px-3 py-2 text-slate-700">Create User</a>
              <a href="/admin/org/teams/new" className="rounded-lg border border-chrome px-3 py-2 text-slate-700">Create Team</a>
            </div>
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

        <section className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Teams and Members" />
          <div className="overflow-hidden rounded-lg border border-chrome">
            <div className="grid grid-cols-[minmax(0,1.4fr)_180px_120px_120px_140px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              <div>Team</div>
              <div>Team Id</div>
              <div>Kind</div>
              <div>Status</div>
              <div>Members</div>
            </div>
            <div className="divide-y divide-chrome">
              {teams.map((team) => (
                <details key={team.id} className="group bg-white">
                  <summary className="grid cursor-pointer grid-cols-[minmax(0,1.4fr)_180px_120px_120px_140px] items-center px-4 py-3 text-sm text-slate-800 marker:hidden">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 transition-transform group-open:rotate-90">▶</span>
                      <div>
                        <a href={`/admin/org/teams/${encodeURIComponent(team.id)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">
                          {team.name}
                        </a>
                        <div className="mt-1 text-xs text-slate-500">Open team to edit settings and memberships</div>
                      </div>
                    </div>
                    <div className="font-mono text-xs text-slate-600">{team.id}</div>
                    <div>{team.kind}</div>
                    <div>{team.status}</div>
                    <div>{team.member_count}</div>
                  </summary>
                  <div className="border-t border-chrome bg-slate-50 px-4 py-4">
                    <div className="overflow-hidden rounded-lg border border-chrome bg-white">
                      <div className="grid grid-cols-[minmax(0,1.2fr)_220px_160px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
                        <div>User</div>
                        <div>Email</div>
                        <div>Team Role</div>
                      </div>
                      <div className="divide-y divide-chrome">
                        {team.members.length ? (
                          team.members.map((member) => (
                            <div key={`${team.id}-${member.user_id}`} className="grid grid-cols-[minmax(0,1.2fr)_220px_160px] px-4 py-3 text-sm text-slate-700">
                              <div>
                                <a href={`/admin/org/users/${encodeURIComponent(member.user_id)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">{member.display_name}</a>
                                <div className="mt-1 font-mono text-xs text-slate-500">{member.user_id}</div>
                              </div>
                              <div>{member.email}</div>
                              <div>{member.role}</div>
                            </div>
                          ))
                        ) : (
                          <div className="px-4 py-4 text-sm text-slate-500">No members yet.</div>
                        )}
                      </div>
                    </div>
                  </div>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Portfolios" />
          <div className="overflow-hidden rounded-lg border border-chrome">
            <div className="grid grid-cols-[minmax(0,1.2fr)_180px_minmax(0,1fr)_120px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              <div>Portfolio</div>
              <div>Portfolio Id</div>
              <div>Scope Teams</div>
              <div>Status</div>
            </div>
            <div className="divide-y divide-chrome">
              {portfolios.map((portfolio) => (
                <div key={portfolio.id} className="grid grid-cols-[minmax(0,1.2fr)_180px_minmax(0,1fr)_120px] px-4 py-3 text-sm text-slate-700">
                  <div>
                    <div className="font-medium text-slate-900">{portfolio.name}</div>
                    <div className="mt-1 text-xs text-slate-500">Owner: {portfolio.owner_team_id}</div>
                  </div>
                  <div className="font-mono text-xs text-slate-600">{portfolio.id}</div>
                  <div>{portfolio.scope_keys.join(", ") || "none"}</div>
                  <div>{portfolio.status}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </PageShell>
  );
}
