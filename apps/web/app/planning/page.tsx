import { getPlanningRoadmap, listPlanningConstructs } from "@/lib/server-api";
import Link from "next/link";

import { Badge, DataTable, FilterPanel, PageShell, appShellProps, formatDate, statusTone } from "../../components/ui-helpers";

function scheduleTone(scheduleState: string): "success" | "neutral" | "warning" | "danger" {
  switch (scheduleState) {
    case "complete":
      return "success";
    case "on_track":
      return "success";
    case "due_soon":
      return "warning";
    case "overdue":
      return "danger";
    default:
      return "neutral";
  }
}

export default async function PlanningPage({
  searchParams,
}: {
  searchParams?: Promise<{ type?: string }>;
}) {
  const filters = (await searchParams) ?? {};
  const [constructs, roadmap] = await Promise.all([
    listPlanningConstructs({ type: filters.type }),
    getPlanningRoadmap({ type: filters.type }),
  ]);
  const overdueCount = roadmap.filter((row) => row.schedule_state === "overdue").length;
  const dueSoonCount = roadmap.filter((row) => row.schedule_state === "due_soon").length;
  const onTrackCount = roadmap.filter((row) => row.schedule_state === "on_track" || row.schedule_state === "complete").length;

  return (
    <PageShell
      {...appShellProps(
        "/planning",
        "Planning",
        "Coordinate governed work into initiatives, releases, milestones, and other higher-order planning constructs."
      )}
    >
      <div className="space-y-4">
        <FilterPanel
          items={[
            { label: "Type", value: filters.type ?? "All" },
            { label: "Constructs", value: String(constructs.length) },
            { label: "Roadmap Rows", value: String(roadmap.length) },
            { label: "On Track", value: String(onTrackCount) },
            { label: "Due Soon", value: String(dueSoonCount), active: dueSoonCount > 0 },
            { label: "Overdue", value: String(overdueCount), active: overdueCount > 0 },
          ]}
          actions={
            <>
              <form action="/planning" className="flex flex-wrap items-end gap-2">
                <div className="grid gap-1">
                  <label htmlFor="planning-type" className="text-xs font-medium text-slate-600">Type</label>
                  <select id="planning-type" name="type" defaultValue={filters.type ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                    <option value="">All</option>
                    <option value="initiative">Initiative</option>
                    <option value="program">Program</option>
                    <option value="release">Release</option>
                    <option value="milestone">Milestone</option>
                    <option value="campaign">Campaign</option>
                  </select>
                </div>
                <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-2 text-sm font-medium text-white">Apply</button>
              </form>
              <Link href="/planning/new" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
                New Planning Construct
              </Link>
            </>
          }
        />
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-xl border border-chrome bg-panel p-4 shadow-panel">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Roadmap Health</div>
            <div className="mt-2 text-2xl font-semibold text-slate-900">{onTrackCount}</div>
            <div className="text-sm text-slate-600">Constructs currently on track or already complete.</div>
          </div>
          <div className="rounded-xl border border-chrome bg-panel p-4 shadow-panel">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Due Soon</div>
            <div className="mt-2 text-2xl font-semibold text-amber-700">{dueSoonCount}</div>
            <div className="text-sm text-slate-600">Constructs that will need near-term sequencing attention.</div>
          </div>
          <div className="rounded-xl border border-chrome bg-panel p-4 shadow-panel">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Overdue</div>
            <div className="mt-2 text-2xl font-semibold text-rose-700">{overdueCount}</div>
            <div className="text-sm text-slate-600">Constructs whose target date has already passed.</div>
          </div>
        </div>
        <DataTable
          data={constructs}
          emptyMessage="No planning constructs found."
          columns={[
            { key: "id", header: "Construct ID", render: (row) => <Link href={`/planning/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            { key: "name", header: "Name", render: (row) => <Link href={`/planning/${row.id}`} className="font-medium text-slate-900 hover:text-accent hover:underline">{row.name}</Link> },
            { key: "type", header: "Type", render: (row) => row.type },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "priority", header: "Priority", render: (row) => String(row.priority) },
            { key: "target", header: "Target", render: (row) => (row.target_date ? formatDate(row.target_date) : "—") },
          ]}
        />
        <DataTable
          data={roadmap}
          emptyMessage="No roadmap rows available."
          columns={[
            { key: "name", header: "Roadmap Item", render: (row) => <Link href={`/planning/${row.id}`} className="font-medium text-slate-900 hover:text-accent hover:underline">{row.name}</Link> },
            { key: "type", header: "Type", render: (row) => row.type },
            { key: "members", header: "Members", render: (row) => String(row.member_count) },
            {
              key: "progress",
              header: "Progress",
              render: (row) => (
                <div className="space-y-1">
                  <div className="text-sm font-medium text-slate-900">{row.completion_pct}% complete</div>
                  <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-slate-950" style={{ width: `${Math.max(6, row.completion_pct)}%` }} />
                  </div>
                  <div className="text-xs text-slate-500">
                    {row.completed_count} done · {row.in_progress_count} active · {row.blocked_count} blocked
                  </div>
                </div>
              ),
            },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "schedule", header: "Schedule", render: (row) => <Badge tone={scheduleTone(row.schedule_state)}>{row.schedule_state.replace("_", " ")}</Badge> },
            { key: "target", header: "Target", render: (row) => (row.target_date ? formatDate(row.target_date) : "—") },
          ]}
        />
      </div>
    </PageShell>
  );
}
