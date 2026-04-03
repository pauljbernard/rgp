import { listPolicies } from "@/lib/server-api";
import { Button, DataTable, PageShell, SectionHeading, Tabs, appShellProps } from "../../../components/ui-helpers";
import { updatePolicyRulesAction } from "./actions";

const TRANSITION_TARGET_OPTIONS = [
  "validation_failed",
  "validated",
  "classified",
  "ownership_resolved",
  "planned",
  "queued",
  "in_execution",
  "awaiting_input",
  "awaiting_review",
  "under_review",
  "changes_requested",
  "approved",
  "rejected",
  "promotion_pending",
  "promoted",
  "completed",
  "failed"
] as const;

const CHECK_NAME_OPTIONS = ["Intake Completeness", "Review Package Readiness", "Approval Freshness"] as const;

export default async function AdminPoliciesPage() {
  const policies = await listPolicies();
  return (
    <PageShell
      {...appShellProps("/admin/policies", "Admin Policies", "Policy bundle and check rule management surface.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <SectionHeading title="Policy Actions" />
            <p className="mt-2 text-sm text-slate-600">
              Review policy bundles in the main catalog. Use this panel to edit enforced transition gates without pushing rule forms into the primary data surface.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Policies</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">{policies.length}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Active</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">
                {policies.filter((policy) => policy.status === "active").length}
              </div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3">
              <div className="text-xs font-medium text-slate-500">Gates</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">
                {policies.reduce((total, policy) => total + policy.transition_gates.length, 0)}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {policies.map((policy) => (
              <form key={policy.id} action={updatePolicyRulesAction} className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
                <input type="hidden" name="policyId" value={policy.id} />
                <div className="mb-3 text-sm font-semibold text-slate-800">{policy.name}</div>
                <div className="space-y-3">
                  {[...policy.transition_gates, { transition_target: "", required_check_name: "" }, { transition_target: "", required_check_name: "" }].map((gate, index) => (
                    <div key={`${policy.id}-${index}`} className="grid gap-3">
                      <label className="space-y-1 text-sm text-slate-700">
                        <span className="block text-xs font-medium text-slate-500">Transition Target</span>
                        <select
                          name="transitionTarget"
                          defaultValue={gate.transition_target}
                          className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
                        >
                          <option value="">Select target</option>
                          {TRANSITION_TARGET_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="space-y-1 text-sm text-slate-700">
                        <span className="block text-xs font-medium text-slate-500">Required Check</span>
                        <select
                          name="requiredCheckName"
                          defaultValue={gate.required_check_name}
                          className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
                        >
                          <option value="">Select check</option>
                          {CHECK_NAME_OPTIONS.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex justify-end">
                  <Button label="Save Rules" tone="primary" type="submit" />
                </div>
              </form>
            ))}
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="policies"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" }
          ]}
        />
        <DataTable
          data={policies}
          emptyMessage="No policies available."
          columns={[
            { key: "name", header: "Name", render: (row) => row.name },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "scope", header: "Scope", render: (row) => row.scope },
            { key: "rules", header: "Transition Gates", render: (row) => (row.rules.length ? row.rules.join(", ") : "None") },
            { key: "updated", header: "Updated At", render: (row) => new Date(row.updated_at).toLocaleString() }
          ]}
        />
      </div>
    </PageShell>
  );
}
