import { getPerformanceOperationsSummary, listPerformanceMetrics, listPerformanceOperationsTrends, listPerformanceRouteSummaries, listPerformanceSloSummaries, listPerformanceTrends } from "@/lib/server-api";
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

function parsePercent(value: string) {
  const normalized = Number(value.replace("%", ""));
  return Number.isFinite(normalized) ? normalized : 0;
}

export default async function PerformanceAnalyticsPage({
  searchParams
}: {
  searchParams: Promise<{ days?: string; route?: string; method?: string; compare_route?: string }>;
}) {
  const { days: daysParam, route, method, compare_route } = await searchParams;
  const days = windowOptions.includes(Number(daysParam) as (typeof windowOptions)[number]) ? Number(daysParam) : 30;
  const [routeSummary, sloSummary, trendResponse, metricResponse, operationsSummary, operationsTrends] = await Promise.all([
    listPerformanceRouteSummaries({ days, page_size: 25 }),
    listPerformanceSloSummaries({ days, page_size: 25 }),
    listPerformanceTrends({ days, route, method, page_size: 100 }),
    listPerformanceMetrics({ days, route, method, page_size: 25 }),
    getPerformanceOperationsSummary(),
    listPerformanceOperationsTrends({ days })
  ]);

  const routeOptions = routeSummary.items.map((item) => item.route);
  const totalRequests = routeSummary.items.reduce((sum, row) => sum + row.request_count, 0);
  const avgP95 = routeSummary.items.length > 0 ? routeSummary.items.reduce((sum, row) => sum + row.p95_duration_ms, 0) / routeSummary.items.length : 0;
  const breaching = sloSummary.items.filter((row) => row.status !== "healthy").length;
  const avgErrorRate = routeSummary.items.length > 0 ? routeSummary.items.reduce((sum, row) => sum + parsePercent(row.error_rate), 0) / routeSummary.items.length : 0;
  const primaryRoute = route ? routeSummary.items.find((item) => item.route == route && (!method || item.method === method)) ?? null : routeSummary.items[0] ?? null;
  const compareRoute = compare_route ? routeSummary.items.find((item) => item.route === compare_route) ?? null : null;
  const primarySlo = primaryRoute ? sloSummary.items.find((item) => item.route === primaryRoute.route && item.method === primaryRoute.method) ?? null : null;
  const compareSlo = compareRoute ? sloSummary.items.find((item) => item.route === compareRoute.route && item.method === compareRoute.method) ?? null : null;

  return (
    <PageShell {...appShellProps("/analytics/performance", "Performance Analytics", "Route latency, reliability, SLO posture, and request-level performance trends.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="performance"
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
              href={`/analytics/performance${buildQuery({ days: option, route, method })}`}
              className={`rounded-full px-3 py-1.5 text-sm ${option === days ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              Last {option}d
            </Link>
          ))}
        </div>
        <FilterPanel
          items={[
            { label: "Time Window", value: `${days}d` },
            { label: "Route", value: route || "All" },
            { label: "Method", value: method || "All" }
          ]}
          actions={
            <form action="/analytics/performance" className="flex flex-wrap items-end gap-2">
              <input type="hidden" name="days" value={days} />
              <div className="grid gap-1">
                <label htmlFor="performance-route" className="text-xs font-medium text-slate-600">Route</label>
                <select id="performance-route" name="route" defaultValue={route ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All routes</option>
                  {routeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="performance-method" className="text-xs font-medium text-slate-600">Method</label>
                <select id="performance-method" name="method" defaultValue={method ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">All methods</option>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                </select>
              </div>
              <div className="grid gap-1">
                <label htmlFor="performance-compare-route" className="text-xs font-medium text-slate-600">Compare Route</label>
                <select id="performance-compare-route" name="compare_route" defaultValue={compare_route ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                  <option value="">None</option>
                  {routeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>
              <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">Apply Filters</button>
              <Link href={`/analytics/performance?days=${days}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">Reset</Link>
            </form>
          }
        />
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <MetricStack
            items={[
              { label: "Requests Observed", value: totalRequests },
              { label: "Avg P95 Latency", value: `${avgP95.toFixed(1)} ms` },
              { label: "SLO Breaches", value: breaching },
              { label: "Avg Error Rate", value: `${avgErrorRate.toFixed(2)}%` }
            ]}
          />
          <div className="grid gap-4">
            <TimeSeriesChart
              title="Latency Trend"
              subtitle="Average and p95 duration across the selected route scope."
              series={[
                { key: "avg_duration", label: "Avg Duration", color: "#2563eb", points: trendResponse.items.map((row) => ({ label: row.period_start, value: row.avg_duration_ms })) },
                { key: "p95_duration", label: "P95 Duration", color: "#0f172a", points: trendResponse.items.map((row) => ({ label: row.period_start, value: row.p95_duration_ms })) }
              ]}
              valueFormatter={(value) => `${value.toFixed(1)} ms`}
            />
            <TimeSeriesChart
              title="Volume and Errors"
              subtitle="Request count and error rate for the selected route scope."
              series={[
                { key: "request_count", label: "Requests", color: "#16a34a", points: trendResponse.items.map((row) => ({ label: row.period_start, value: row.request_count })) },
                { key: "error_rate", label: "Error Rate", color: "#dc2626", points: trendResponse.items.map((row) => ({ label: row.period_start, value: parsePercent(row.error_rate) })) }
              ]}
            />
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <MetricStack
            items={[
              { label: "Queued Checks", value: operationsSummary.queued_checks },
              { label: "Running Checks", value: operationsSummary.running_checks },
              { label: "Waiting Runs", value: operationsSummary.waiting_runs },
              { label: "Failed Runs", value: operationsSummary.failed_runs },
              { label: "Stale Reviews", value: operationsSummary.stale_reviews },
              { label: "Pending Promotions", value: operationsSummary.pending_promotions },
              { label: "Avg Check Queue", value: `${operationsSummary.avg_check_queue_minutes.toFixed(1)} min` },
              { label: "Avg Runtime Queue", value: `${operationsSummary.avg_runtime_queue_minutes.toFixed(1)} min` }
            ]}
          />
          <div className="grid gap-4">
            <TimeSeriesChart
              title="Queue Pressure"
              subtitle="Worker and governance backlog signals over time."
              series={[
                { key: "queued_checks", label: "Queued Checks", color: "#0f172a", points: operationsTrends.map((row) => ({ label: row.period_start, value: row.queued_checks })) },
                { key: "waiting_runs", label: "Waiting Runs", color: "#2563eb", points: operationsTrends.map((row) => ({ label: row.period_start, value: row.waiting_runs })) },
                { key: "pending_promotions", label: "Pending Promotions", color: "#16a34a", points: operationsTrends.map((row) => ({ label: row.period_start, value: row.pending_promotions })) }
              ]}
            />
            <TimeSeriesChart
              title="Operational Risk Trend"
              subtitle="Failures and stale human work that can slow delivery."
              series={[
                { key: "failed_runs", label: "Failed Runs", color: "#dc2626", points: operationsTrends.map((row) => ({ label: row.period_start, value: row.failed_runs })) },
                { key: "stale_reviews", label: "Stale Reviews", color: "#d97706", points: operationsTrends.map((row) => ({ label: row.period_start, value: row.stale_reviews })) },
                { key: "running_checks", label: "Running Checks", color: "#7c3aed", points: operationsTrends.map((row) => ({ label: row.period_start, value: row.running_checks })) }
              ]}
            />
          </div>
        </div>
        <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Route Comparison</h2>
            <div className="text-sm text-slate-600">{primaryRoute?.route ?? "Primary"} vs {compareRoute?.route ?? "None"}</div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Primary</div>
              <div className="mt-2 text-sm text-slate-700">Requests: {primaryRoute?.request_count ?? 0}</div>
              <div className="mt-1 text-sm text-slate-700">P95: {primaryRoute ? `${primaryRoute.p95_duration_ms.toFixed(1)} ms` : "n/a"}</div>
              <div className="mt-1 text-sm text-slate-700">Error Rate: {primaryRoute?.error_rate ?? "n/a"}</div>
              <div className="mt-1 text-sm text-slate-700">SLO Status: {primarySlo?.status ?? "n/a"}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Comparison</div>
              <div className="mt-2 text-sm text-slate-700">Requests: {compareRoute?.request_count ?? 0}</div>
              <div className="mt-1 text-sm text-slate-700">P95: {compareRoute ? `${compareRoute.p95_duration_ms.toFixed(1)} ms` : "n/a"}</div>
              <div className="mt-1 text-sm text-slate-700">Error Rate: {compareRoute?.error_rate ?? "n/a"}</div>
              <div className="mt-1 text-sm text-slate-700">SLO Status: {compareSlo?.status ?? "n/a"}</div>
            </div>
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <DataTable
            data={routeSummary.items}
            emptyMessage="No route performance summaries available."
            columns={[
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "method", header: "Method", render: (row) => row.method },
              { key: "requests", header: "Requests", render: (row) => row.request_count },
              { key: "avg", header: "Avg Duration", render: (row) => `${row.avg_duration_ms.toFixed(1)} ms` },
              { key: "p95", header: "P95 Duration", render: (row) => `${row.p95_duration_ms.toFixed(1)} ms` },
              { key: "errors", header: "Error Rate", render: (row) => row.error_rate }
            ]}
          />
          <DataTable
            data={sloSummary.items}
            emptyMessage="No SLO summaries available."
            columns={[
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "method", header: "Method", render: (row) => row.method },
              { key: "availability", header: "Availability", render: (row) => row.availability_actual },
              { key: "latency_slo", header: "Latency SLO", render: (row) => `${row.latency_slo_ms} ms` },
              { key: "budget", header: "Error Budget Remaining", render: (row) => row.error_budget_remaining },
              { key: "status", header: "Status", render: (row) => row.status }
            ]}
          />
        </div>
        <DataTable
          data={metricResponse.items}
          emptyMessage="No raw performance metrics available."
          columns={[
            { key: "route", header: "Route", render: (row) => row.route },
            { key: "method", header: "Method", render: (row) => row.method },
            { key: "status_code", header: "Status", render: (row) => row.status_code },
            { key: "duration", header: "Duration", render: (row) => `${row.duration_ms.toFixed(1)} ms` },
            { key: "trace", header: "Trace", render: (row) => row.trace_id ?? "n/a" },
            { key: "occurred", header: "Occurred", render: (row) => new Date(row.occurred_at).toLocaleString() }
          ]}
        />
      </div>
    </PageShell>
  );
}
