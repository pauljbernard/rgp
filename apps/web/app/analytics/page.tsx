import {
  listDeliveryDoraScoped,
  listDeliveryLifecycleScoped,
  listDeliveryTrends,
  listPerformanceRouteSummaries,
  listPerformanceSloSummaries,
  listPerformanceTrends,
  listPortfolioSummaries,
  listWorkflowTrends
} from "@/lib/server-api";
import Link from "next/link";
import { DataTable, MetricStack, PageShell, Tabs, TimeSeriesChart, appShellProps } from "../../components/ui-helpers";

export default async function AnalyticsPage() {
  const [deliveryTrends, doraRows, lifecycleRows, routeSummary, sloSummary, performanceTrends, portfolioSummaries, workflowTrends] = await Promise.all([
    listDeliveryTrends({ days: 30 }),
    listDeliveryDoraScoped(),
    listDeliveryLifecycleScoped(),
    listPerformanceRouteSummaries({ days: 30, page_size: 10 }),
    listPerformanceSloSummaries({ days: 30, page_size: 10 }),
    listPerformanceTrends({ days: 30, page_size: 30 }),
    listPortfolioSummaries(),
    listWorkflowTrends({ days: 30 })
  ]);

  const totalThroughput = deliveryTrends.reduce((sum, row) => sum + row.throughput_count, 0);
  const totalDeployments = deliveryTrends.reduce((sum, row) => sum + row.deployment_count, 0);
  const totalFailures = deliveryTrends.reduce((sum, row) => sum + row.failed_count, 0);
  const avgLead = deliveryTrends.length > 0 ? deliveryTrends.reduce((sum, row) => sum + row.lead_time_hours, 0) / deliveryTrends.length : 0;
  const avgP95 = routeSummary.items.length > 0 ? routeSummary.items.reduce((sum, row) => sum + row.p95_duration_ms, 0) / routeSummary.items.length : 0;
  const sloBreaches = sloSummary.items.filter((row) => row.status !== "healthy").length;

  return (
    <PageShell {...appShellProps("/analytics", "Analytics Overview", "Cross-cutting delivery, performance, and portfolio intelligence with direct drill-down into the detailed report pages.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="overview"
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
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">
          <MetricStack
            items={[
              { label: "Throughput (30d)", value: totalThroughput },
              { label: "Deployments (30d)", value: totalDeployments },
              { label: "Failures (30d)", value: totalFailures },
              { label: "Avg Lead Time", value: `${avgLead.toFixed(1)}h` },
              { label: "Avg P95 Latency", value: `${avgP95.toFixed(1)} ms` },
              { label: "SLO Breaches", value: sloBreaches }
            ]}
          />
          <div className="grid gap-4">
            <TimeSeriesChart
              title="Delivery and Workflow Volume"
              subtitle="Top-level movement in throughput, deployments, and workflow requests over the last 30 days."
              series={[
                { key: "throughput", label: "Throughput", color: "#0f172a", points: deliveryTrends.map((row) => ({ label: row.period_start, value: row.throughput_count })) },
                { key: "deployments", label: "Deployments", color: "#2563eb", points: deliveryTrends.map((row) => ({ label: row.period_start, value: row.deployment_count })) },
                { key: "workflow_requests", label: "Workflow Requests", color: "#16a34a", points: workflowTrends.map((row) => ({ label: row.period_start, value: row.request_count })) }
              ]}
            />
            <TimeSeriesChart
              title="Performance and Delivery Risk"
              subtitle="Lead time, failures, and route latency summarized in one executive view."
              series={[
                { key: "lead_time", label: "Lead Time (h)", color: "#d97706", points: deliveryTrends.map((row) => ({ label: row.period_start, value: row.lead_time_hours })) },
                { key: "failures", label: "Failures", color: "#dc2626", points: deliveryTrends.map((row) => ({ label: row.period_start, value: row.failed_count })) },
                { key: "avg_latency", label: "Avg Latency (ms)", color: "#7c3aed", points: performanceTrends.items.map((row) => ({ label: row.period_start, value: row.avg_duration_ms })) }
              ]}
            />
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-3">
          <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Delivery</h2>
              <Link href="/analytics/delivery" className="text-sm text-accent">Open</Link>
            </div>
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <div>DORA rows: {doraRows.length}</div>
              <div>Lifecycle rows: {lifecycleRows.length}</div>
              <div>Top scope: {doraRows[0] ? `${doraRows[0].scope_type}: ${doraRows[0].scope_key}` : "n/a"}</div>
            </div>
          </div>
          <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Performance</h2>
              <Link href="/analytics/performance" className="text-sm text-accent">Open</Link>
            </div>
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <div>Routes tracked: {routeSummary.items.length}</div>
              <div>SLO entries: {sloSummary.items.length}</div>
              <div>Breaches: {sloBreaches}</div>
            </div>
          </div>
          <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Portfolios</h2>
              <Link href="/analytics/workflows" className="text-sm text-accent">Explore</Link>
            </div>
            <div className="mt-4 space-y-2 text-sm text-slate-600">
              <div>Portfolios tracked: {portfolioSummaries.length}</div>
              <div>Active requests: {portfolioSummaries.reduce((sum, row) => sum + row.active_request_count, 0)}</div>
              <div>Deployments: {portfolioSummaries.reduce((sum, row) => sum + row.deployment_count, 0)}</div>
            </div>
          </div>
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <DataTable
            data={portfolioSummaries}
            emptyMessage="No portfolio summaries available."
            columns={[
              { key: "portfolio", header: "Portfolio", render: (row) => row.portfolio_name },
              { key: "requests", header: "Requests", render: (row) => row.request_count },
              { key: "active", header: "Active", render: (row) => row.active_request_count },
              { key: "completed", header: "Completed", render: (row) => row.completed_request_count },
              { key: "deployments", header: "Deployments", render: (row) => row.deployment_count }
            ]}
          />
          <DataTable
            data={routeSummary.items}
            emptyMessage="No performance routes available."
            columns={[
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "requests", header: "Requests", render: (row) => row.request_count },
              { key: "p95", header: "P95", render: (row) => `${row.p95_duration_ms.toFixed(1)} ms` },
              { key: "error_rate", header: "Error Rate", render: (row) => row.error_rate },
              { key: "apdex", header: "Apdex", render: (row) => row.apdex }
            ]}
          />
        </div>
      </div>
    </PageShell>
  );
}
