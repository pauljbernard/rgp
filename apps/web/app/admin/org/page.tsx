import { getCurrentPrincipal, listAdminOrganizations, listAdminPortfolios, listAdminTeams, listAdminTenants, listAdminUsers } from "@/lib/server-api";
import { PageShell, SectionHeading, Tabs, appShellProps } from "../../../components/ui-helpers";

function renderTeam(team: Awaited<ReturnType<typeof listAdminTeams>>[number]) {
  return (
    <details key={team.id} className="overflow-hidden rounded-lg border border-chrome bg-white">
      <summary className="grid cursor-pointer grid-cols-[minmax(0,1.2fr)_180px_120px_120px_140px] items-center px-4 py-3 text-sm text-slate-800 marker:hidden">
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">▶</span>
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
  );
}

export default async function AdminOrgPage() {
  const principal = await getCurrentPrincipal();
  const isPlatformAdmin = principal.roles.includes("platform_admin");
  const [users, organizations, teams, portfolios, tenants] = await Promise.all([
    listAdminUsers(),
    listAdminOrganizations(),
    listAdminTeams(),
    listAdminPortfolios(),
    isPlatformAdmin ? listAdminTenants() : Promise.resolve([]),
  ]);
  const assignedUserIds = new Set(teams.flatMap((team) => team.members.map((member) => member.user_id)));
  const unassignedUsers = users.filter((user) => !assignedUserIds.has(user.id));

  return (
    <PageShell
      {...appShellProps("/admin/org", "Admin Organization", isPlatformAdmin ? "Platform-wide tenant, organization, team, and user administration." : "Tenant-scoped organization, team, and user administration.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <SectionHeading title="Catalog Summary" />
            <p className="mt-2 text-sm text-slate-600">
              {isPlatformAdmin
                ? "Platform admins manage the full tenant hierarchy. Tenant admins remain scoped to the organizations, teams, and users inside their own tenant."
                : "You are operating as a tenant admin. The main panel is limited to your tenant's organizations, teams, users, and portfolios."}
            </p>
          </div>

          <div className={`grid gap-3 ${isPlatformAdmin ? "grid-cols-4" : "grid-cols-3"}`}>
            {isPlatformAdmin ? (
              <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
                <div className="text-xs font-medium text-slate-500">Tenants</div>
                <div className="mt-1 text-2xl font-semibold text-slate-900">{tenants.length}</div>
              </div>
            ) : null}
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Organizations</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{organizations.length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Teams</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{teams.length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Users</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{users.length}</div>
            </div>
          </div>

          <div className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
            <SectionHeading title="Management Pages" />
            <div className="flex flex-col gap-2 text-sm">
              {isPlatformAdmin ? <a href="/admin/org/tenants/new" className="rounded-lg border border-chrome px-3 py-2 text-slate-700">Create Tenant</a> : null}
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
          <SectionHeading title={isPlatformAdmin ? "Tenants, Organizations, Teams, and Members" : "Organizations, Teams, and Members"} />
          <div className="overflow-hidden rounded-lg border border-chrome">
            {isPlatformAdmin ? (
              <>
                <div className="grid grid-cols-[minmax(0,1.5fr)_180px_120px_140px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
                  <div>Tenant</div>
                  <div>Tenant Id</div>
                  <div>Status</div>
                  <div>Organizations</div>
                </div>
                <div className="divide-y divide-chrome">
                  {tenants.map((tenant) => {
                    const tenantOrganizations = organizations.filter((organization) => organization.tenant_id === tenant.id);
                    return (
                      <details key={tenant.id} className="group bg-white">
                        <summary className="grid cursor-pointer grid-cols-[minmax(0,1.5fr)_180px_120px_140px] items-center px-4 py-3 text-sm text-slate-800 marker:hidden">
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500 transition-transform group-open:rotate-90">▶</span>
                            <div>
                              <a href={`/admin/org/tenants/${encodeURIComponent(tenant.id)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">{tenant.name}</a>
                              <div className="mt-1 text-xs text-slate-500">Open tenant to maintain top-level tenant settings.</div>
                            </div>
                          </div>
                          <div className="font-mono text-xs text-slate-600">{tenant.id}</div>
                          <div>{tenant.status}</div>
                          <div>{tenantOrganizations.length}</div>
                        </summary>
                        <div className="border-t border-chrome bg-slate-50 px-4 py-4">
                          <div className="space-y-3">
                            {tenantOrganizations.map((organization) => {
                              const organizationTeams = teams.filter((team) => team.organization_id === organization.id);
                              return (
                                <details key={organization.id} className="group overflow-hidden rounded-lg border border-chrome bg-white">
                                  <summary className="grid cursor-pointer grid-cols-[minmax(0,1.5fr)_180px_120px_140px] items-center px-4 py-3 text-sm text-slate-800 marker:hidden">
                                    <div className="flex items-center gap-3">
                                      <span className="text-xs text-slate-500 transition-transform group-open:rotate-90">▶</span>
                                      <div>
                                        <div className="font-medium text-slate-900">{organization.name}</div>
                                        <div className="mt-1 text-xs text-slate-500">Organizations contain teams, and users belong to one or more teams.</div>
                                      </div>
                                    </div>
                                    <div className="font-mono text-xs text-slate-600">{organization.id}</div>
                                    <div>{organization.status}</div>
                                    <div>{organizationTeams.length}</div>
                                  </summary>
                                  <div className="border-t border-chrome bg-slate-50 px-4 py-4">
                                    <div className="space-y-3">
                                      {organizationTeams.length ? organizationTeams.map(renderTeam) : (
                                        <div className="rounded-lg border border-dashed border-chrome bg-white px-4 py-4 text-sm text-slate-500">No teams are assigned to this organization.</div>
                                      )}
                                    </div>
                                  </div>
                                </details>
                              );
                            })}
                          </div>
                        </div>
                      </details>
                    );
                  })}
                </div>
              </>
            ) : (
              <>
                <div className="grid grid-cols-[minmax(0,1.5fr)_180px_120px_140px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
                  <div>Organization</div>
                  <div>Organization Id</div>
                  <div>Status</div>
                  <div>Teams</div>
                </div>
                <div className="divide-y divide-chrome">
                  {organizations.map((organization) => {
                    const organizationTeams = teams.filter((team) => team.organization_id === organization.id);
                    return (
                      <details key={organization.id} className="group bg-white">
                        <summary className="grid cursor-pointer grid-cols-[minmax(0,1.5fr)_180px_120px_140px] items-center px-4 py-3 text-sm text-slate-800 marker:hidden">
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500 transition-transform group-open:rotate-90">▶</span>
                            <div>
                              <div className="font-medium text-slate-900">{organization.name}</div>
                              <div className="mt-1 text-xs text-slate-500">Organizations contain teams, and users belong to one or more teams.</div>
                            </div>
                          </div>
                          <div className="font-mono text-xs text-slate-600">{organization.id}</div>
                          <div>{organization.status}</div>
                          <div>{organizationTeams.length}</div>
                        </summary>
                        <div className="border-t border-chrome bg-slate-50 px-4 py-4">
                          <div className="space-y-3">
                            {organizationTeams.length ? organizationTeams.map(renderTeam) : (
                              <div className="rounded-lg border border-dashed border-chrome bg-white px-4 py-4 text-sm text-slate-500">No teams are assigned to this organization.</div>
                            )}
                          </div>
                        </div>
                      </details>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </section>

        <section className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Unassigned Users" />
          <p className="text-sm text-slate-600">
            Users created through registration or administration are shown here until they are assigned to one or more teams.
          </p>
          <div className="overflow-hidden rounded-lg border border-chrome">
            <div className="grid grid-cols-[minmax(0,1.1fr)_220px_140px_140px_180px] bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              <div>User</div>
              <div>Email</div>
              <div>Status</div>
              <div>Password</div>
              <div>Registration Source</div>
            </div>
            <div className="divide-y divide-chrome">
              {unassignedUsers.length ? (
                unassignedUsers.map((user) => (
                  <div key={user.id} className="grid grid-cols-[minmax(0,1.1fr)_220px_140px_140px_180px] px-4 py-3 text-sm text-slate-700">
                    <div>
                      <a href={`/admin/org/users/${encodeURIComponent(user.id)}`} className="font-medium text-slate-900 underline-offset-2 hover:underline">
                        {user.display_name}
                      </a>
                      <div className="mt-1 font-mono text-xs text-slate-500">{user.id}</div>
                      {isPlatformAdmin ? <div className="mt-1 text-xs text-slate-500">Tenant: {user.tenant_id}</div> : null}
                    </div>
                    <div>{user.email}</div>
                    <div>{user.status}</div>
                    <div>{user.has_password ? "configured" : user.password_reset_required ? "reset required" : "not set"}</div>
                    <div className="font-mono text-xs text-slate-600">{user.registration_request_id ?? "manual"}</div>
                  </div>
                ))
              ) : (
                <div className="px-4 py-4 text-sm text-slate-500">All users are currently assigned to at least one team.</div>
              )}
            </div>
          </div>
        </section>

        <section className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Portfolios" />
          <div className="overflow-hidden rounded-lg border border-chrome">
            <div className={`grid ${isPlatformAdmin ? "grid-cols-[minmax(0,1.2fr)_180px_120px_minmax(0,1fr)_120px]" : "grid-cols-[minmax(0,1.2fr)_180px_minmax(0,1fr)_120px]"} bg-slate-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.08em] text-slate-500`}>
              <div>Portfolio</div>
              <div>Portfolio Id</div>
              {isPlatformAdmin ? <div>Tenant</div> : null}
              <div>Scope Teams</div>
              <div>Status</div>
            </div>
            <div className="divide-y divide-chrome">
              {portfolios.map((portfolio) => (
                <div key={portfolio.id} className={`grid ${isPlatformAdmin ? "grid-cols-[minmax(0,1.2fr)_180px_120px_minmax(0,1fr)_120px]" : "grid-cols-[minmax(0,1.2fr)_180px_minmax(0,1fr)_120px]"} px-4 py-3 text-sm text-slate-700`}>
                  <div>
                    <div className="font-medium text-slate-900">{portfolio.name}</div>
                    <div className="mt-1 text-xs text-slate-500">Owner: {portfolio.owner_team_id}</div>
                  </div>
                  <div className="font-mono text-xs text-slate-600">{portfolio.id}</div>
                  {isPlatformAdmin ? <div>{portfolio.tenant_id}</div> : null}
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
