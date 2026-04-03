import { getDeliveryForecast, listDeliveryDoraScoped, listDeliveryForecastPoints, listDeliveryLifecycleScoped, listDeliveryTrends, listPortfolios, listTeams, listUsers } from "@/lib/server-api";
import Link from "next/link";
import { DataTable, FilterPanel, MetricStack, PageShell, Tabs, TimeSeriesChart, appShellProps } from "../../../components/ui-helpers";

const windowOptions = [7, 30, 90] as const;

function buildQuery(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export default async function DeliveryAnalyticsPage({
  searchParams
}: {
  searchParams: Promise<{ days?: string; team_id?: string; user_id?: string; portfolio_id?: string; compare_team_id?: string; compare_portfolio_id?: string }>;
}) {
  const { days: daysParam, team_id, user_id, portfolio_id, compare_team_id, compare_portfolio_id } = await searchParams;
  const days = windowOptions.includes(Number(daysParam) as (typeof windowOptions)[number]) ? Number(daysParam) : 30;
  const [doraRows, lifecycleRows, trendRows, teams, users, portfolios, compareDoraRows, compareLifecycleRows, forecastSummary, forecastPoints] = await Promise.all([
    listDeliveryDoraScoped({ portfolio_id, team_id, user_id }),
    listDeliveryLifecycleScoped({ portfolio_id, team_id, user_id }),
    listDeliveryTrends({ days, portfolio_id, team_id, user_id }),
    listTeams(),
    listUsers(),
    listPortfolios(),
    compare_team_id || compare_portfolio_id ? listDeliveryDoraScoped({ portfolio_id: compare_portfolio_id, team_id: compare_team_id }) : Promise.resolve([]),
    compare_team_id || compare_portfolio_id ? listDeliveryLifecycleScoped({ portfolio_id: compare_portfolio_id, team_id: compare_team_id }) : Promise.resolve([]),
    getDeliveryForecast({ days, portfolio_id, team_id, user_id, forecast_days: 14 }),
    listDeliveryForecastPoints({ days, portfolio_id, team_id, user_id, forecast_days: 14 })
  ]);

  const activeTeam = teams.find((item) => item.id === team_id)?.name ?? "All";
  const activeUser = users.find((item) => item.id === user_id)?.display_name ?? "All";
  const activePortfolio = portfolios.find((item) => item.id === portfolio_id)?.name ?? "All";
  const compareLabel =
    portfolios.find((item) => item.id === compare_portfolio_id)?.name ??
    teams.find((item) => item.id === compare_team_id)?.name ??
    "None";
  const throughput = trendRows.reduce((sum, row) => sum + row.throughput_count, 0);
  const deployments = trendRows.reduce((sum, row) => sum + row.deployment_count, 0);
  const avgLead = trendRows.length > 0 ? trendRows.reduce((sum, row) => sum + row.lead_time_hours, 0) / trendRows.length : 0;
  const failures = trendRows.reduce((sum, row) => sum + row.failed_count, 0);

  return (
    <PageShell {...appShellProps("/analytics/delivery", "Delivery Analytics", "DORA-style delivery intelligence with lifecycle timing and throughput trends across portfolios, teams, and users.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="delivery"
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
              href={`/analytics/delivery${buildQuery({ days: option, team_id, user_id, portfolio_id })}`}
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
            <form action="/analytics/delivery" className="flex flex-wrap items-end gap-2">
              <input type="hidden" name="days" value={days} />
              <div className="grid gap-1">
                <label htmlFor="delivery-portfolio" className="text-xs font-medium text-slate-600">Portfolio</label>
                <select id="delivery-portfolio" name="portfolio_id" defaultValue={portfolio_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All portfolios</option>
                  {portfolios.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="delivery-team" className="text-xs font-medium text-slate-600">Team</label>
                <select id="delivery-team" name="team_id" defaultValue={team_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All teams</option>
                  {teams.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="delivery-user" className="text-xs font-medium text-slate-600">User</label>
                <select id="delivery-user" name="user_id" defaultValue={user_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All users</option>
                  {users.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="delivery-compare-portfolio" className="text-xs font-medium text-slate-600">Compare Portfolio</label>
                <select id="delivery-compare-portfolio" name="compare_portfolio_id" defaultValue={compare_portfolio_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">None</option>
                  {portfolios.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="delivery-compare-team" className="text-xs font-medium text-slate-600">Compare Team</label>
                <select id="delivery-compare-team" name="compare_team_id" defaultValue={compare_team_id ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">None</option>
                  {teams.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                </select>
              </div>
              <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">Apply Filters</button>
              <Link href={`/analytics/delivery?days=${days}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">Reset</Link>
            </form>
          }
        />
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <MetricStack
            items={[
              { label: "Throughput", value: throughput },
              { label: "Deployments", value: deployments },
              { label: "Avg Lead Time", value: `${avgLead.toFixed(1)}h` },
              { label: "Failures", value: failures }
            ]}
          />
          <div className="grid gap-4">
            <TimeSeriesChart
              title="Delivery Throughput"
              subtitle="Completed work, deployments, and total throughput over time."
              series={[
                { key: "throughput", label: "Throughput", color: "#0f172a", points: trendRows.map((row) => ({ label: row.period_start, value: row.throughput_count })) },
                { key: "completed", label: "Completed", color: "#16a34a", points: trendRows.map((row) => ({ label: row.period_start, value: row.completed_count })) },
                { key: "deployments", label: "Deployments", color: "#2563eb", points: trendRows.map((row) => ({ label: row.period_start, value: row.deployment_count })) }
              ]}
            />
            <TimeSeriesChart
              title="Lead Time and Failure Trend"
              subtitle="Lead time movement and daily failures for the selected scope."
              series={[
                { key: "lead_time", label: "Lead Time (h)", color: "#d97706", points: trendRows.map((row) => ({ label: row.period_start, value: row.lead_time_hours })) },
                { key: "failures", label: "Failures", color: "#dc2626", points: trendRows.map((row) => ({ label: row.period_start, value: row.failed_count })) }
              ]}
              valueFormatter={(value) => `${value.toFixed(1)}h`}
            />
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <MetricStack
            items={[
              { label: "Forecast Window", value: `${forecastSummary.forecast_days}d` },
              { label: "Avg Daily Throughput", value: forecastSummary.avg_daily_throughput.toFixed(2) },
              { label: "Avg Daily Deployments", value: forecastSummary.avg_daily_deployments.toFixed(2) },
              { label: "Projected Throughput", value: forecastSummary.projected_total_throughput.toFixed(1) },
              { label: "Projected Deployments", value: forecastSummary.projected_total_deployments.toFixed(1) },
              { label: "Projected Lead Time", value: `${forecastSummary.projected_lead_time_hours.toFixed(1)}h` }
            ]}
          />
          <div className="grid gap-4">
            <TimeSeriesChart
              title="Forecast Throughput and Deployments"
              subtitle="Forward projection based on recent delivery trend history."
              series={[
                { key: "forecast_throughput", label: "Projected Throughput", color: "#0f172a", points: forecastPoints.map((row) => ({ label: row.period_start, value: row.projected_throughput_count })) },
                { key: "forecast_deployments", label: "Projected Deployments", color: "#2563eb", points: forecastPoints.map((row) => ({ label: row.period_start, value: row.projected_deployment_count })) }
              ]}
            />
            <TimeSeriesChart
              title="Forecast Lead Time"
              subtitle="Projected average lead time for the selected scope."
              series={[
                { key: "forecast_lead_time", label: "Projected Lead Time (h)", color: "#d97706", points: forecastPoints.map((row) => ({ label: row.period_start, value: row.projected_lead_time_hours })) }
              ]}
              valueFormatter={(value) => `${value.toFixed(1)}h`}
            />
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Scope Comparison</h2>
              <div className="text-sm text-slate-600">Primary vs {compareLabel}</div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-chrome bg-slate-50 p-4">
                <div className="text-xs font-medium text-slate-500">Primary</div>
                <div className="mt-2 text-sm text-slate-700">Throughput: {throughput}</div>
                <div className="mt-1 text-sm text-slate-700">Lead Time: {avgLead.toFixed(1)}h</div>
                <div className="mt-1 text-sm text-slate-700">DORA Rows: {doraRows.length}</div>
              </div>
              <div className="rounded-lg border border-chrome bg-slate-50 p-4">
                <div className="text-xs font-medium text-slate-500">Comparison</div>
                <div className="mt-2 text-sm text-slate-700">
                  Throughput: {compareLifecycleRows.reduce((sum, row) => sum + row.throughput_30d, 0)}
                </div>
                <div className="mt-1 text-sm text-slate-700">
                  Lead Time: {compareDoraRows.length > 0 ? (compareDoraRows.reduce((sum, row) => sum + row.lead_time_hours, 0) / compareDoraRows.length).toFixed(1) : "0.0"}h
                </div>
                <div className="mt-1 text-sm text-slate-700">DORA Rows: {compareDoraRows.length}</div>
              </div>
            </div>
          </div>
          <DataTable
            data={doraRows}
            emptyMessage="No DORA analytics available."
            columns={[
              { key: "scope", header: "Scope", render: (row) => `${row.scope_type}: ${row.scope_key}` },
              { key: "deploy_freq", header: "Deployment Frequency", render: (row) => row.deployment_frequency },
              { key: "lead_time", header: "Lead Time (h)", render: (row) => row.lead_time_hours.toFixed(2) },
              { key: "cfr", header: "Change Failure Rate", render: (row) => row.change_failure_rate },
              { key: "mttr", header: "MTTR (h)", render: (row) => row.mean_time_to_restore_hours.toFixed(2) }
            ]}
          />
          <DataTable
            data={lifecycleRows}
            emptyMessage="No lifecycle analytics available."
            columns={[
              { key: "scope", header: "Scope", render: (row) => `${row.scope_type}: ${row.scope_key}` },
              { key: "throughput", header: "Throughput 30d", render: (row) => row.throughput_30d },
              { key: "cycle", header: "Cycle Time (h)", render: (row) => row.cycle_time_hours.toFixed(2) },
              { key: "review", header: "Review Time (h)", render: (row) => row.review_time_hours.toFixed(2) },
              { key: "promotion", header: "Promotion Time (h)", render: (row) => row.promotion_time_hours.toFixed(2) }
            ]}
          />
        </div>
      </div>
    </PageShell>
  );
}
