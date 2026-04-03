import { listAgentAnalytics, listAgentTrends, listPortfolios, listTeams, listUsers, listWorkflowAnalytics, listWorkflowTrends } from "@/lib/server-api";
import Link from "next/link";
import { DataTable, FilterPanel, MetricStack, PageShell, Tabs, TimeSeriesChart, appShellProps } from "../../../components/ui-helpers";

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

function parseCurrency(value: string) {
  const normalized = Number(value.replace(/[^0-9.]+/g, ""));
  return Number.isFinite(normalized) ? normalized : 0;
}

export default async function AnalyticsCostPage({
  searchParams
}: {
  searchParams: Promise<{ days?: string; team_id?: string; user_id?: string; portfolio_id?: string; compare_team_id?: string; compare_portfolio_id?: string }>;
}) {
  const { days: daysParam, team_id, user_id, portfolio_id, compare_team_id, compare_portfolio_id } = await searchParams;
  const days = windowOptions.includes(Number(daysParam) as (typeof windowOptions)[number]) ? Number(daysParam) : 30;
  const [workflowRows, workflowTrends, agentRows, agentTrends, teams, users, portfolios, compareWorkflowRows, compareAgentRows] = await Promise.all([
    listWorkflowAnalytics({ days, team_id, user_id, portfolio_id }),
    listWorkflowTrends({ days, team_id, user_id, portfolio_id }),
    listAgentAnalytics({ days, team_id, user_id, portfolio_id }),
    listAgentTrends({ days, team_id, user_id, portfolio_id }),
    listTeams(),
    listUsers(),
    listPortfolios(),
    compare_team_id || compare_portfolio_id ? listWorkflowAnalytics({ days, team_id: compare_team_id, portfolio_id: compare_portfolio_id }) : Promise.resolve([]),
    compare_team_id || compare_portfolio_id ? listAgentAnalytics({ days, team_id: compare_team_id, portfolio_id: compare_portfolio_id }) : Promise.resolve([])
  ]);

  const workflowTrendSeries = workflowTrends.map((point) => ({
    label: point.period_start,
    value: Number((point.request_count * point.cost_per_execution).toFixed(2))
  }));
  const agentSpendSeries = agentTrends.map((point) => ({
    label: point.period_start,
    value: Number((point.invocation_count * (1.25 + point.avg_duration_minutes * 0.35)).toFixed(2))
  }));

  const totalWorkflowSpend = workflowTrendSeries.reduce((sum, point) => sum + point.value, 0);
  const totalAgentSpend = agentSpendSeries.reduce((sum, point) => sum + point.value, 0);
  const avgWorkflowCost = workflowRows.length > 0 ? workflowRows.reduce((sum, row) => sum + parseCurrency(row.cost_per_execution), 0) / workflowRows.length : 0;
  const avgAgentCost = agentRows.length > 0 ? agentRows.reduce((sum, row) => sum + parseCurrency(row.cost_per_invocation), 0) / agentRows.length : 0;
  const compareAvgWorkflowCost =
    compareWorkflowRows.length > 0 ? compareWorkflowRows.reduce((sum, row) => sum + parseCurrency(row.cost_per_execution), 0) / compareWorkflowRows.length : 0;
  const compareAvgAgentCost =
    compareAgentRows.length > 0 ? compareAgentRows.reduce((sum, row) => sum + parseCurrency(row.cost_per_invocation), 0) / compareAgentRows.length : 0;

  const activeTeam = teams.find((item) => item.id === team_id)?.name ?? "All";
  const activeUser = users.find((item) => item.id === user_id)?.display_name ?? "All";
  const activePortfolio = portfolios.find((item) => item.id === portfolio_id)?.name ?? "All";
  const compareLabel =
    portfolios.find((item) => item.id === compare_portfolio_id)?.name ??
    teams.find((item) => item.id === compare_team_id)?.name ??
    "None";

  return (
    <PageShell {...appShellProps("/analytics/cost", "Cost Analytics", "Estimated spend, efficiency, and cost movement over time across workflows and agents.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="cost"
          tabs={[
            { key: "overview", label: "Overview", href: "/analytics" },
            { key: "workflows", label: "Workflows", href: "/analytics/workflows" },
            { key: "agents", label: "Agents", href: "/analytics/agents" },
            { key: "bottlenecks", label: "Bottlenecks", href: "/analytics/bottlenecks" },
            { key: "delivery", label: "Delivery", href: "/analytics/delivery" },
            { key: "performance", label: "Performance", href: "/analytics/performance" },
            { key: "cost", label: "Cost", href: "/analytics/cost" }
          ]}
        />
        <div className="flex flex-wrap gap-2">
          {windowOptions.map((option) => (
            <Link
              key={option}
              href={`/analytics/cost${buildQuery({ days: option, team_id, user_id, portfolio_id })}`}
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
            { label: "User", value: activeUser }
          ]}
          actions={
            <form action="/analytics/cost" className="flex flex-wrap items-end gap-2">
              <input type="hidden" name="days" value={days} />
              <div className="grid gap-1">
                <label htmlFor="cost-portfolio" className="text-xs font-medium text-slate-600">
                  Portfolio
                </label>
                <select id="cost-portfolio" name="portfolio_id" defaultValue={portfolio_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All portfolios</option>
                  {portfolios.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="cost-team" className="text-xs font-medium text-slate-600">
                  Team
                </label>
                <select id="cost-team" name="team_id" defaultValue={team_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All teams</option>
                  {teams.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="cost-user" className="text-xs font-medium text-slate-600">
                  User
                </label>
                <select id="cost-user" name="user_id" defaultValue={user_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All users</option>
                  {users.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.display_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="cost-compare-portfolio" className="text-xs font-medium text-slate-600">
                  Compare Portfolio
                </label>
                <select id="cost-compare-portfolio" name="compare_portfolio_id" defaultValue={compare_portfolio_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">None</option>
                  {portfolios.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="cost-compare-team" className="text-xs font-medium text-slate-600">
                  Compare Team
                </label>
                <select id="cost-compare-team" name="compare_team_id" defaultValue={compare_team_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">None</option>
                  {teams.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">
                Apply Filters
              </button>
              <Link href={`/analytics/cost?days=${days}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
                Reset
              </Link>
            </form>
          }
        />
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <MetricStack
            items={[
              { label: "Estimated Workflow Spend", value: `$${totalWorkflowSpend.toFixed(2)}` },
              { label: "Estimated Agent Spend", value: `$${totalAgentSpend.toFixed(2)}` },
              { label: "Avg Workflow Cost / Execution", value: `$${avgWorkflowCost.toFixed(2)}` },
              { label: "Avg Agent Cost / Invocation", value: `$${avgAgentCost.toFixed(2)}` }
            ]}
          />
          <div className="grid gap-4">
            <TimeSeriesChart
              title="Estimated Spend Over Time"
              subtitle="Daily spend estimates derived from workflow executions and agent invocations."
              series={[
                {
                  key: "workflow_spend",
                  label: "Workflow Spend",
                  color: "#0f172a",
                  points: workflowTrendSeries
                },
                {
                  key: "agent_spend",
                  label: "Agent Spend",
                  color: "#2563eb",
                  points: agentSpendSeries
                }
              ]}
              valueFormatter={(value) => `$${value.toFixed(2)}`}
            />
            <TimeSeriesChart
              title="Cost Efficiency Trend"
              subtitle="How execution count and unit cost are moving under the selected reporting filters."
              series={[
                {
                  key: "cost_per_execution",
                  label: "Cost / Execution",
                  color: "#d97706",
                  points: workflowTrends.map((point) => ({ label: point.period_start, value: point.cost_per_execution }))
                },
                {
                  key: "invocation_volume",
                  label: "Agent Invocations",
                  color: "#16a34a",
                  points: agentTrends.map((point) => ({ label: point.period_start, value: point.invocation_count }))
                }
              ]}
              valueFormatter={(value) => value >= 10 ? `${value.toFixed(0)}` : `$${value.toFixed(2)}`}
            />
          </div>
        </div>
        <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Cost Comparison</h2>
            <div className="text-sm text-slate-600">Primary vs {compareLabel}</div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Primary</div>
              <div className="mt-2 text-sm text-slate-700">Workflow Cost / Execution: ${avgWorkflowCost.toFixed(2)}</div>
              <div className="mt-1 text-sm text-slate-700">Agent Cost / Invocation: ${avgAgentCost.toFixed(2)}</div>
              <div className="mt-1 text-sm text-slate-700">Estimated Spend: ${(totalWorkflowSpend + totalAgentSpend).toFixed(2)}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Comparison</div>
              <div className="mt-2 text-sm text-slate-700">Workflow Cost / Execution: ${compareAvgWorkflowCost.toFixed(2)}</div>
              <div className="mt-1 text-sm text-slate-700">Agent Cost / Invocation: ${compareAvgAgentCost.toFixed(2)}</div>
              <div className="mt-1 text-sm text-slate-700">Workflow Rows: {compareWorkflowRows.length}</div>
            </div>
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <DataTable
            data={workflowRows}
            emptyMessage="No workflow cost analytics available."
            columns={[
              { key: "workflow", header: "Workflow", render: (row) => <Link href={`/requests?workflow=${encodeURIComponent(row.workflow)}`} className="text-accent">{row.workflow}</Link> },
              { key: "cost", header: "Cost / Execution", render: (row) => row.cost_per_execution },
              { key: "avg_cycle", header: "Avg Cycle Time", render: (row) => row.avg_cycle_time },
              { key: "failure", header: "Failure Rate", render: (row) => row.failure_rate },
              { key: "trend", header: "Trend", render: (row) => row.trend }
            ]}
          />
          <DataTable
            data={agentRows}
            emptyMessage="No agent cost analytics available."
            columns={[
              { key: "agent", header: "Agent", render: (row) => <Link href={`/runs?owner=${encodeURIComponent(row.agent)}`} className="text-accent">{row.agent}</Link> },
              { key: "cost", header: "Cost / Invocation", render: (row) => row.cost_per_invocation },
              { key: "invocations", header: "Invocations", render: (row) => row.invocations },
              { key: "duration", header: "Avg Duration", render: (row) => row.avg_duration },
              { key: "quality", header: "Quality Score", render: (row) => row.quality_score }
            ]}
          />
        </div>
      </div>
    </PageShell>
  );
}
