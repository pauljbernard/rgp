import { listAgentAnalytics, listAgentTrends, listPortfolios, listTeams, listUsers } from "@/lib/server-api";
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

export default async function AgentAnalyticsPage({
  searchParams
}: {
  searchParams: Promise<{ days?: string; team_id?: string; user_id?: string; portfolio_id?: string; agent?: string }>;
}) {
  const { days: daysParam, team_id, user_id, portfolio_id, agent } = await searchParams;
  const days = windowOptions.includes(Number(daysParam) as (typeof windowOptions)[number]) ? Number(daysParam) : 30;
  const [rows, trends, teams, users, portfolios] = await Promise.all([
    listAgentAnalytics({ days, team_id, user_id, portfolio_id }),
    listAgentTrends({ days, team_id, user_id, portfolio_id, agent }),
    listTeams(),
    listUsers(),
    listPortfolios()
  ]);

  const activeTeam = teams.find((item) => item.id === team_id)?.name ?? "All";
  const activeUser = users.find((item) => item.id === user_id)?.display_name ?? "All";
  const activePortfolio = portfolios.find((item) => item.id === portfolio_id)?.name ?? "All";

  return (
    <PageShell {...appShellProps("/analytics/agents", "Agent Analytics", "Invocation, quality, and cost performance for agents over time.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="agents"
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
              href={`/analytics/agents${buildQuery({ days: option, team_id, user_id, portfolio_id, agent })}`}
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
            { label: "Agent", value: agent || "All" }
          ]}
          actions={
            <form action="/analytics/agents" className="flex flex-wrap items-end gap-2">
              <input type="hidden" name="days" value={days} />
              <div className="grid gap-1">
                <label htmlFor="agent-portfolio" className="text-xs font-medium text-slate-600">
                  Portfolio
                </label>
                <select id="agent-portfolio" name="portfolio_id" defaultValue={portfolio_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All portfolios</option>
                  {portfolios.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="agent-team" className="text-xs font-medium text-slate-600">
                  Team
                </label>
                <select id="agent-team" name="team_id" defaultValue={team_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All teams</option>
                  {teams.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="agent-user" className="text-xs font-medium text-slate-600">
                  User
                </label>
                <select id="agent-user" name="user_id" defaultValue={user_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All users</option>
                  {users.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.display_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="agent-filter" className="text-xs font-medium text-slate-600">
                  Agent
                </label>
                <select id="agent-filter" name="agent" defaultValue={agent ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All agents</option>
                  {rows.map((item) => (
                    <option key={item.agent} value={item.agent}>
                      {item.agent}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">
                Apply Filters
              </button>
              <Link href={`/analytics/agents?days=${days}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
                Reset
              </Link>
            </form>
          }
        />
        <div className="grid gap-4 xl:grid-cols-2">
          <TimeSeriesChart
            title="Agent Invocation Trend"
            subtitle="Daily invocation volume and retry rate for the selected scope."
            series={[
              {
                key: "invocations",
                label: "Invocations",
                color: "#0f172a",
                points: trends.map((point) => ({ label: point.period_start, value: point.invocation_count }))
              },
              {
                key: "retry_rate",
                label: "Retry Rate",
                color: "#d97706",
                points: trends.map((point) => ({ label: point.period_start, value: point.retry_rate }))
              }
            ]}
          />
          <TimeSeriesChart
            title="Agent Quality Trend"
            subtitle="Daily success, duration, and quality movement for the selected scope."
            series={[
              {
                key: "success_rate",
                label: "Success Rate",
                color: "#2563eb",
                points: trends.map((point) => ({ label: point.period_start, value: point.success_rate }))
              },
              {
                key: "quality_score",
                label: "Quality Score",
                color: "#16a34a",
                points: trends.map((point) => ({ label: point.period_start, value: point.quality_score }))
              }
            ]}
          />
        </div>
        <DataTable
          data={rows}
          emptyMessage="No agent analytics available."
          columns={[
            { key: "agent", header: "Agent", render: (row) => <Link href={`/runs?owner=${encodeURIComponent(row.agent)}`} className="text-accent">{row.agent}</Link> },
            { key: "invocations", header: "Invocations", render: (row) => row.invocations },
            { key: "success", header: "Success Rate", render: (row) => row.success_rate },
            { key: "retry", header: "Retry Rate", render: (row) => row.retry_rate },
            { key: "duration", header: "Avg Duration", render: (row) => row.avg_duration },
            { key: "cost", header: "Cost per Invocation", render: (row) => row.cost_per_invocation },
            { key: "quality", header: "Quality Score", render: (row) => row.quality_score },
            { key: "drilldown", header: "Drill Down", render: (row) => <Link href={`/runs?owner=${encodeURIComponent(row.agent)}`} className="text-accent">View runs</Link> }
          ]}
        />
      </div>
    </PageShell>
  );
}
