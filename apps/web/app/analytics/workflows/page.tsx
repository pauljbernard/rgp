import { listPortfolios, listTeams, listUsers, listWorkflowAnalytics, listWorkflowTrends } from "@/lib/server-api";
import Link from "next/link";
import { DataTable, FilterPanel, PageShell, Tabs, TimeSeriesChart, appShellProps } from "../../../components/ui-helpers";

const windowOptions = [7, 30, 90] as const;

function buildQuery(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export default async function WorkflowAnalyticsPage({
  searchParams
}: {
  searchParams: Promise<{ days?: string; team_id?: string; user_id?: string; portfolio_id?: string; workflow?: string }>;
}) {
  const { days: daysParam, team_id, user_id, portfolio_id, workflow } = await searchParams;
  const days = windowOptions.includes(Number(daysParam) as (typeof windowOptions)[number]) ? Number(daysParam) : 30;
  const [rows, trends, teams, users, portfolios] = await Promise.all([
    listWorkflowAnalytics({ days, team_id, user_id, portfolio_id }),
    listWorkflowTrends({ days, team_id, user_id, portfolio_id, workflow }),
    listTeams(),
    listUsers(),
    listPortfolios()
  ]);

  const activeTeam = teams.find((item) => item.id === team_id)?.name ?? "All";
  const activeUser = users.find((item) => item.id === user_id)?.display_name ?? "All";
  const activePortfolio = portfolios.find((item) => item.id === portfolio_id)?.name ?? "All";

  return (
    <PageShell
      {...appShellProps(
        "/analytics/workflows",
        "Workflow Analytics",
        "Trend-aware workflow performance analysis with organization, portfolio, team, and user filters."
      )}
    >
      <div className="space-y-4">
        <Tabs
          activeKey="workflows"
          tabs={[
            { key: "overview", label: "Overview", href: "/analytics" },
            { key: "workflows", label: "Workflows", href: "/analytics/workflows" },
            { key: "agents", label: "Agents", href: "/analytics/agents" },
            { key: "delivery", label: "Delivery", href: "/analytics/delivery" },
            { key: "performance", label: "Performance", href: "/analytics/performance" },
            { key: "bottlenecks", label: "Bottlenecks", href: "/analytics/bottlenecks" },
            { key: "cost", label: "Cost", href: "/analytics/cost" }
          ]}
        />
        <div className="flex flex-wrap gap-2">
          {windowOptions.map((option) => (
            <Link
              key={option}
              href={`/analytics/workflows${buildQuery({ days: option, team_id, user_id, portfolio_id, workflow })}`}
              className={`rounded-full px-3 py-1.5 text-sm ${option === days ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              Last {option}d
            </Link>
          ))}
        </div>
        <FilterPanel
          items={[
            { label: "Time Window", value: `${days}d` },
            { label: "Portfolio", value: activePortfolio },
            { label: "Team", value: activeTeam },
            { label: "User", value: activeUser },
            { label: "Workflow", value: workflow || "All" }
          ]}
          actions={
            <>
              <form action="/analytics/workflows" className="flex flex-wrap items-end gap-2">
                <input type="hidden" name="days" value={days} />
                <div className="grid gap-1">
                  <label htmlFor="workflow-portfolio" className="text-xs font-medium text-slate-600">
                    Portfolio
                  </label>
                  <select id="workflow-portfolio" name="portfolio_id" defaultValue={portfolio_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                    <option value="">All portfolios</option>
                    {portfolios.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-1">
                  <label htmlFor="workflow-team" className="text-xs font-medium text-slate-600">
                    Team
                  </label>
                  <select id="workflow-team" name="team_id" defaultValue={team_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                    <option value="">All teams</option>
                    {teams.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-1">
                  <label htmlFor="workflow-user" className="text-xs font-medium text-slate-600">
                    User
                  </label>
                  <select id="workflow-user" name="user_id" defaultValue={user_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                    <option value="">All users</option>
                    {users.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-1">
                  <label htmlFor="workflow-filter" className="text-xs font-medium text-slate-600">
                    Workflow
                  </label>
                  <select id="workflow-filter" name="workflow" defaultValue={workflow ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                    <option value="">All workflows</option>
                    {rows.map((item) => (
                      <option key={item.workflow} value={item.workflow}>
                        {item.workflow}
                      </option>
                    ))}
                  </select>
                </div>
                <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">
                  Apply Filters
                </button>
                <Link href={`/analytics/workflows?days=${days}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
                  Reset
                </Link>
              </form>
            </>
          }
        />
        <div className="grid gap-4 xl:grid-cols-2">
          <TimeSeriesChart
            title="Workflow Volume"
            subtitle="Daily request counts for the selected reporting scope."
            series={[
              {
                key: "request_count",
                label: "Requests",
                color: "#0f172a",
                points: trends.map((point) => ({ label: point.period_start, value: point.request_count }))
              },
              {
                key: "failed_count",
                label: "Failures",
                color: "#dc2626",
                points: trends.map((point) => ({ label: point.period_start, value: point.failed_count }))
              }
            ]}
          />
          <TimeSeriesChart
            title="Cycle Time"
            subtitle="Average cycle time in hours for the selected reporting scope."
            series={[
              {
                key: "avg_cycle",
                label: "Avg Cycle Hours",
                color: "#2563eb",
                points: trends.map((point) => ({ label: point.period_start, value: point.avg_cycle_time_hours }))
              },
              {
                key: "review_stale",
                label: "Stale Reviews",
                color: "#d97706",
                points: trends.map((point) => ({ label: point.period_start, value: point.review_stale_count }))
              }
            ]}
            valueFormatter={(value: number) => `${value.toFixed(1)}h`}
          />
        </div>
        <DataTable
          data={rows}
          emptyMessage="No workflow analytics available."
          columns={[
            {
              key: "workflow",
              header: "Workflow",
              render: (row) => (
                <div className="space-y-1">
                  <div><Link href={`/runs?workflow=${encodeURIComponent(row.workflow)}`} className="text-accent">{row.workflow}</Link></div>
                  <div><Link href={`/analytics/workflows/${encodeURIComponent(row.workflow)}/federation`} className="text-xs text-slate-600 hover:text-accent">Open federation view</Link></div>
                  <div><Link href={`/analytics/workflows/${encodeURIComponent(row.workflow)}/history`} className="text-xs text-slate-600 hover:text-accent">Open workflow history</Link></div>
                </div>
              )
            },
            { key: "avg", header: "Avg Cycle Time", render: (row) => row.avg_cycle_time },
            { key: "p95", header: "P95 Duration", render: (row) => row.p95_duration },
            { key: "failure", header: "Failure Rate", render: (row) => row.failure_rate },
            { key: "review", header: "Review Delay", render: (row) => row.review_delay },
            {
              key: "federation",
              header: "Federation",
              render: (row) => (
                <div className="space-y-1">
                  <div>{row.federated_projection_count} projection{row.federated_projection_count === 1 ? "" : "s"}</div>
                  <div>{row.federated_coverage} coverage</div>
                  <div>{row.federated_conflict_count} conflict{row.federated_conflict_count === 1 ? "" : "s"}</div>
                </div>
              )
            },
            { key: "cost", header: "Cost per Execution", render: (row) => row.cost_per_execution },
            { key: "trend", header: "Trend", render: (row) => row.trend },
            {
              key: "drilldown",
              header: "Drill Down",
              render: (row) => (
                <div className="space-y-1">
                  <div><Link href={`/requests?workflow=${encodeURIComponent(row.workflow)}`} className="text-accent">View requests</Link></div>
                  <div><Link href={`/runs?workflow=${encodeURIComponent(row.workflow)}&federation=with_conflict`} className="text-accent">View federated conflicts</Link></div>
                  <div><Link href={`/analytics/workflows/${encodeURIComponent(row.workflow)}/federation?federation=with_conflict`} className="text-accent">Open federation control</Link></div>
                  <div><Link href={`/analytics/workflows/${encodeURIComponent(row.workflow)}/history`} className="text-accent">Open workflow history</Link></div>
                </div>
              )
            }
          ]}
        />
      </div>
    </PageShell>
  );
}
