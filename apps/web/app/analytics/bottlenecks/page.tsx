import { listBottleneckAnalytics } from "@/lib/server-api";
import Link from "next/link";
import { DataTable, PageShell, Tabs, appShellProps } from "../../../components/ui-helpers";

const windowOptions = [7, 30, 90] as const;

export default async function BottleneckAnalyticsPage({ searchParams }: { searchParams: Promise<{ days?: string }> }) {
  const { days: daysParam } = await searchParams;
  const days = windowOptions.includes(Number(daysParam) as (typeof windowOptions)[number]) ? Number(daysParam) : 30;
  const rows = await listBottleneckAnalytics(days);
  return (
    <PageShell {...appShellProps("/analytics/bottlenecks", "Bottleneck Analytics", "Operational bottleneck analysis for workflow steps and reviewer delay.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="bottlenecks"
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
              href={`/analytics/bottlenecks?days=${option}`}
              className={`rounded-full px-3 py-1.5 text-sm ${option === days ? "bg-slate-950 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              Last {option}d
            </Link>
          ))}
        </div>
        <DataTable
          data={rows}
          emptyMessage="No bottleneck analytics available."
          columns={[
            {
              key: "workflow",
              header: "Workflow",
              render: (row) => (
                <Link
                  href={
                    row.workflow === "Review Queue"
                      ? "/reviews/queue?blocking_only=true"
                      : `/runs?workflow=${encodeURIComponent(row.workflow)}&status=waiting`
                  }
                  className="text-accent"
                >
                  {row.workflow}
                </Link>
              )
            },
            { key: "step", header: "Step", render: (row) => row.step },
            { key: "wait", header: "Avg Wait Time", render: (row) => row.avg_wait_time },
            { key: "blocks", header: "Block Count", render: (row) => row.block_count },
            { key: "reviewer", header: "Reviewer Delay", render: (row) => row.reviewer_delay },
            { key: "trend", header: "Trend", render: (row) => row.trend },
            {
              key: "drilldown",
              header: "Drill Down",
              render: (row) => (
                <Link
                  href={
                    row.workflow === "Review Queue"
                      ? "/reviews/queue?blocking_only=true"
                      : `/runs?workflow=${encodeURIComponent(row.workflow)}&status=waiting`
                  }
                  className="text-accent"
                >
                  Open source
                </Link>
              )
            }
          ]}
        />
      </div>
    </PageShell>
  );
}
