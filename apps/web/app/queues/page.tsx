import { listAssignmentGroups, listEscalationRules, listSlaBreaches, listSlaDefinitions } from "@/lib/server-api";

import { DataTable, PageShell, SectionHeading, appShellProps } from "../../components/ui-helpers";
import { createAssignmentGroupAction, createEscalationRuleAction, createSlaDefinitionAction, remediateSlaBreachAction } from "./actions";

export default async function QueuesPage() {
  const [groups, slaDefinitions, escalationRules, slaBreaches] = await Promise.all([
    listAssignmentGroups(),
    listSlaDefinitions(),
    listEscalationRules(),
    listSlaBreaches(),
  ]);
  const activeGroups = groups.filter((group) => group.status === "active").length;
  const constrainedGroups = groups.filter((group) => group.max_capacity !== null && group.current_load >= group.max_capacity).length;
  const activeEscalations = escalationRules.filter((rule) => rule.status === "active").length;

  return (
    <PageShell
      {...appShellProps("/queues", "Queues", "Govern assignment groups, routing readiness, and service commitments.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Queue Summary" />
          <div className="grid gap-2">
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Active Groups</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{activeGroups}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">At Capacity</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{constrainedGroups}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">SLA Definitions</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{slaDefinitions.length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-white px-3 py-2">
              <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Escalation Rules</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">{activeEscalations}</div>
            </div>
          </div>
          <form action={createAssignmentGroupAction} className="grid gap-2">
            <div className="grid gap-1">
              <label htmlFor="queue-group-name" className="text-xs font-medium text-slate-600">Assignment Group</label>
              <input id="queue-group-name" name="name" placeholder="Editorial Reviewers" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-1">
              <label htmlFor="queue-group-skills" className="text-xs font-medium text-slate-600">Skill Tags</label>
              <input id="queue-group-skills" name="skillTags" placeholder="editorial, review, legal" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-1">
              <label htmlFor="queue-group-capacity" className="text-xs font-medium text-slate-600">Max Capacity</label>
              <input id="queue-group-capacity" name="maxCapacity" type="number" min="1" placeholder="8" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <button type="submit" className="w-full rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
              Create Assignment Group
            </button>
          </form>
          <form action={createEscalationRuleAction} className="grid gap-2">
            <div className="grid gap-1">
              <label htmlFor="queue-escalation-name" className="text-xs font-medium text-slate-600">Escalation Rule</label>
              <input id="queue-escalation-name" name="name" placeholder="Stale Review Escalation" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-1">
              <label htmlFor="queue-escalation-status" className="text-xs font-medium text-slate-600">Status Condition</label>
              <input id="queue-escalation-status" name="statusValue" placeholder="awaiting_review" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-1">
              <label htmlFor="queue-escalation-target" className="text-xs font-medium text-slate-600">Escalation Target</label>
              <input id="queue-escalation-target" name="escalationTarget" placeholder="queue_lead" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <button type="submit" className="w-full rounded-md border border-chrome bg-white px-4 py-2 text-sm font-medium text-slate-700">
              Create Escalation Rule
            </button>
          </form>
          <form action={createSlaDefinitionAction} className="grid gap-2">
            <div className="grid gap-1">
              <label htmlFor="queue-sla-name" className="text-xs font-medium text-slate-600">SLA Definition</label>
              <input id="queue-sla-name" name="name" placeholder="Assessment Review SLA" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-2 grid-cols-2">
              <input name="scopeType" defaultValue="request_type" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="scopeId" placeholder="assessment" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-2 grid-cols-3">
              <input name="responseTargetHours" type="number" min="1" placeholder="4" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="resolutionTargetHours" type="number" min="1" placeholder="24" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
              <input name="reviewDeadlineHours" type="number" min="1" placeholder="8" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <button type="submit" className="w-full rounded-md border border-chrome bg-white px-4 py-2 text-sm font-medium text-slate-700">
              Create SLA Definition
            </button>
          </form>
        </div>
      }
    >
      <div className="space-y-4">
        <DataTable
          data={groups}
          emptyMessage="No assignment groups are configured."
          columns={[
            { key: "name", header: "Assignment Group", render: (row) => row.name },
            { key: "skills", header: "Skill Tags", render: (row) => row.skill_tags.join(", ") || "—" },
            { key: "capacity", header: "Capacity", render: (row) => (row.max_capacity === null ? "Unbounded" : `${row.current_load}/${row.max_capacity}`) },
            { key: "status", header: "Status", render: (row) => row.status },
          ]}
        />
        <DataTable
          data={slaDefinitions}
          emptyMessage="No SLA definitions are configured."
          columns={[
            { key: "name", header: "SLA Definition", render: (row) => row.name },
            { key: "scope", header: "Scope", render: (row) => (row.scope_id ? `${row.scope_type}: ${row.scope_id}` : row.scope_type) },
            { key: "response", header: "Response", render: (row) => (row.response_target_hours === null ? "—" : `${row.response_target_hours}h`) },
            { key: "resolution", header: "Resolution", render: (row) => (row.resolution_target_hours === null ? "—" : `${row.resolution_target_hours}h`) },
            { key: "review", header: "Review", render: (row) => (row.review_deadline_hours === null ? "—" : `${row.review_deadline_hours}h`) },
          ]}
        />
        <DataTable
          data={escalationRules}
          emptyMessage="No escalation rules are configured."
          columns={[
            { key: "name", header: "Escalation Rule", render: (row) => row.name },
            { key: "type", header: "Type", render: (row) => row.escalation_type },
            { key: "target", header: "Target", render: (row) => row.escalation_target },
            { key: "delay", header: "Delay", render: (row) => `${row.delay_minutes}m` },
            { key: "status", header: "Status", render: (row) => row.status },
          ]}
        />
        <DataTable
          data={slaBreaches}
          emptyMessage="No SLA breaches have been recorded."
          columns={[
            { key: "request", header: "Request", render: (row) => row.request_id },
            { key: "type", header: "Breach Type", render: (row) => row.breach_type },
            { key: "severity", header: "Severity", render: (row) => row.severity },
            { key: "actual", header: "Actual", render: (row) => `${row.actual_hours}h` },
            { key: "target", header: "Target", render: (row) => `${row.target_hours}h` },
            {
              key: "remediation",
              header: "Remediation",
              render: (row) =>
                row.remediation_action ? (
                  row.remediation_action
                ) : (
                  <form action={remediateSlaBreachAction}>
                    <input type="hidden" name="breachId" value={row.id} />
                    <input type="hidden" name="remediationAction" value="queue_lead_notified" />
                    <button type="submit" className="rounded-md border border-chrome bg-white px-3 py-1 text-xs font-medium text-slate-700">
                      Notify Queue Lead
                    </button>
                  </form>
                )
            },
          ]}
        />
      </div>
    </PageShell>
  );
}
