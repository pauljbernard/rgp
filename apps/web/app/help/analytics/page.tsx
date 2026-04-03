import { PageShell } from "../../../components/ui-helpers";
import { HelpSection, HelpTabs, HelpTable, helpShellProps } from "../help-shared";

const analyticsPages = [
  { page: "Analytics Overview", route: "/analytics", purpose: "Cross-cutting summary of delivery, performance, and portfolio posture." },
  { page: "Workflows", route: "/analytics/workflows", purpose: "Workflow volume, timing, and trend reporting." },
  { page: "Agents", route: "/analytics/agents", purpose: "Agent invocation, retry, and operational reporting." },
  { page: "Delivery", route: "/analytics/delivery", purpose: "DORA-style delivery metrics, lifecycle timing, throughput, comparisons, and forecasts." },
  { page: "Performance", route: "/analytics/performance", purpose: "Latency, volume, SLO posture, queue pressure, and operational risk." },
  { page: "Cost", route: "/analytics/cost", purpose: "Estimated spend, efficiency, and cost movement over time." },
  { page: "Bottlenecks", route: "/analytics/bottlenecks", purpose: "Operational bottleneck analysis." }
];

const analyticsFilters = [
  { filter: "Days", use: "Sets the reporting time window." },
  { filter: "Portfolio", use: "Scopes analytics to one portfolio or comparison target." },
  { filter: "Team", use: "Scopes analytics to one owning team or comparison target." },
  { filter: "User", use: "Scopes analytics to one user where supported." },
  { filter: "Workflow or Agent", use: "Narrows reporting to a specific workflow family or integrated agent." },
  { filter: "Route / Method", use: "Used on performance pages to narrow metrics to one API path or method." }
];

export default function HelpAnalyticsPage() {
  return (
    <PageShell
      {...helpShellProps("Help: Analytics", "Guidance for operational reports, time-series charts, filters, comparisons, and forecasting surfaces.")}
      contextPanel={
        <div className="space-y-5 text-sm text-slate-600">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Reporting Rule</h2>
            <p className="mt-2">
              Analytics summarize governed work. Use them to find trends and outliers, then drill back into the request, run, review, or promotion record when you need authoritative detail.
            </p>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpTabs activeKey="analytics" />
        <HelpSection title="Analytics Pages" description="These are the reporting pages available to logged-in users.">
          <HelpTable
            data={analyticsPages}
            columns={[
              { key: "page", header: "Page", render: (row) => row.page },
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "purpose", header: "Purpose", render: (row) => row.purpose }
            ]}
          />
        </HelpSection>
        <HelpSection title="Common Filters and Controls" description="Most analytics pages share a filter model so users can compare consistent slices of work over time.">
          <HelpTable
            data={analyticsFilters}
            columns={[
              { key: "filter", header: "Filter", render: (row) => row.filter },
              { key: "use", header: "What It Does", render: (row) => row.use }
            ]}
          />
        </HelpSection>
        <HelpSection title="How To Read The Charts" description="The analytics area is chart-first, but charts are paired with tables so the same slice of data is available as both trend and row-level summary.">
          <div className="grid gap-3 text-sm text-slate-700">
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use the chart to see how a measure changes over time.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use the table below the chart to inspect the same measure in row form.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use comparison controls where present to compare one portfolio, team, route, or reporting slice against another.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use delivery forecast views for forward-looking estimates, not as a replacement for actual governed outcomes.</div>
          </div>
        </HelpSection>
      </div>
    </PageShell>
  );
}
