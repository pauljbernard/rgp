import { getPlanningConstruct } from "@/lib/server-api";

import { Badge, DataTable, PageShell, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";
import { addPlanningMembershipAction, nudgePlanningMembershipAction, removePlanningMembershipAction, updatePlanningMembershipAction } from "../actions";

export default async function PlanningConstructDetailPage({
  params,
}: {
  params: Promise<{ constructId: string }>;
}) {
  const { constructId } = await params;
  const detail = await getPlanningConstruct(constructId);
  const { construct, memberships, progress } = detail;
  const totalMembers = memberships.length;

  return (
    <PageShell
      {...appShellProps("/planning", construct.name, "Inspect governed planning membership, progress, and roadmap readiness.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Construct State" />
          <div className="space-y-2 text-sm text-slate-700">
            <div>Status: <Badge tone={statusTone(construct.status)}>{construct.status}</Badge></div>
            <div>Type: {construct.type}</div>
            <div>Priority: {construct.priority}</div>
            <div>Owner Team: {construct.owner_team_id || "—"}</div>
            <div>Target Date: {construct.target_date ? formatDate(construct.target_date) : "—"}</div>
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Members</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{progress.total}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Completion</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{progress.completion_pct}%</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Completed</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{progress.status_counts.completed ?? 0}</div>
            </div>
          </div>
          <form action={addPlanningMembershipAction} className="grid gap-2">
            <input type="hidden" name="constructId" value={construct.id} />
            <div className="grid gap-1">
              <label htmlFor="planning-request-id" className="text-xs font-medium text-slate-600">Add Request</label>
              <input id="planning-request-id" name="requestId" placeholder="req_..." className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-2 grid-cols-2">
              <input name="sequence" type="number" min="0" defaultValue="0" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="priority" type="number" min="0" defaultValue="0" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <button type="submit" className="w-full rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
              Add Request to Construct
            </button>
          </form>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Summary</h2>
          <p className="mt-2 text-sm text-slate-700">{construct.description || "No description provided."}</p>
        </div>
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Progress Breakdown</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-4">
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Submitted</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{progress.status_counts.submitted ?? 0}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Active</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{(progress.status_counts.in_progress ?? 0) + (progress.status_counts.awaiting_review ?? 0)}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Blocked</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{progress.status_counts.blocked ?? 0}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Closed</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{(progress.status_counts.completed ?? 0) + (progress.status_counts.closed ?? 0)}</div>
            </div>
          </div>
        </div>
        <DataTable
          data={memberships}
          emptyMessage="No requests have been attached to this construct."
          columns={[
            { key: "request", header: "Request ID", render: (row) => row.request_id },
            {
              key: "sequence",
              header: "Sequence",
              render: (row) => (
                <form action={updatePlanningMembershipAction} className="flex items-center gap-2">
                  <input type="hidden" name="constructId" value={construct.id} />
                  <input type="hidden" name="requestId" value={row.request_id} />
                  <input name="sequence" type="number" min="0" defaultValue={row.sequence} className="w-20 rounded-md border border-chrome bg-white px-2 py-1 text-xs" />
                  <input name="priority" type="hidden" value={row.priority} />
                  <button type="submit" className="rounded-md border border-chrome px-2 py-1 text-xs font-medium text-slate-700">Save</button>
                </form>
              ),
            },
            {
              key: "priority",
              header: "Priority",
              render: (row) => (
                <form action={updatePlanningMembershipAction} className="flex items-center gap-2">
                  <input type="hidden" name="constructId" value={construct.id} />
                  <input type="hidden" name="requestId" value={row.request_id} />
                  <input name="priority" type="number" min="0" defaultValue={row.priority} className="w-20 rounded-md border border-chrome bg-white px-2 py-1 text-xs" />
                  <input name="sequence" type="hidden" value={row.sequence} />
                  <button type="submit" className="rounded-md border border-chrome px-2 py-1 text-xs font-medium text-slate-700">Save</button>
                </form>
              ),
            },
            { key: "added", header: "Added", render: (row) => (row.added_at ? formatDate(row.added_at) : "—") },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="flex flex-wrap gap-2">
                  <form action={nudgePlanningMembershipAction}>
                    <input type="hidden" name="constructId" value={construct.id} />
                    <input type="hidden" name="requestId" value={row.request_id} />
                    <input type="hidden" name="currentSequence" value={row.sequence} />
                    <input type="hidden" name="priority" value={row.priority} />
                    <input type="hidden" name="direction" value="earlier" />
                    <button type="submit" disabled={row.sequence <= 0} className="rounded-md border border-chrome px-2 py-1 text-xs font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
                      Move Earlier
                    </button>
                  </form>
                  <form action={nudgePlanningMembershipAction}>
                    <input type="hidden" name="constructId" value={construct.id} />
                    <input type="hidden" name="requestId" value={row.request_id} />
                    <input type="hidden" name="currentSequence" value={row.sequence} />
                    <input type="hidden" name="priority" value={row.priority} />
                    <input type="hidden" name="direction" value="later" />
                    <button type="submit" disabled={totalMembers <= 1} className="rounded-md border border-chrome px-2 py-1 text-xs font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50">
                      Move Later
                    </button>
                  </form>
                  <form action={removePlanningMembershipAction}>
                    <input type="hidden" name="constructId" value={construct.id} />
                    <input type="hidden" name="requestId" value={row.request_id} />
                    <button type="submit" className="rounded-md border border-rose-200 bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700">
                      Remove
                    </button>
                  </form>
                </div>
              ),
            },
          ]}
        />
      </div>
    </PageShell>
  );
}
