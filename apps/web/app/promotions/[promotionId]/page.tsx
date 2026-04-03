import { getPromotion } from "@/lib/server-api";
import { Button, DataTable, PageShell, PromotionGate, appShellProps } from "../../../components/ui-helpers";
import { RefreshOnCheckRunEvents } from "../../../components/refresh-on-check-run-events";
import { evaluatePromotionCheckAction, overridePromotionApprovalAction, overridePromotionCheckAction, promotionAction, runPromotionChecksAction } from "./actions";

export default async function PromotionPage({ params }: { params: Promise<{ promotionId: string }> }) {
  const { promotionId } = await params;
  const promotion = await getPromotion(promotionId);
  const hasPendingChecks = promotion.check_runs.some((item) => item.status === "queued" || item.status === "running");

  return (
    <PageShell {...appShellProps("/promotions/pro_001", "Promotion Gate", "Final governed acceptance screen for promotion readiness and execution.")}>
      <RefreshOnCheckRunEvents promotionId={promotion.id} active={hasPendingChecks} />
      <div className="space-y-4">
        <PromotionGate
          checks={promotion.required_checks}
          approvals={promotion.required_approvals}
          target={promotion.target}
          readiness={promotion.execution_readiness}
        />
        <div className="flex flex-wrap gap-2 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <form action={promotionAction}>
            <input type="hidden" name="promotionId" value={promotion.id} />
            <input type="hidden" name="action" value="dry_run" />
            <Button label="Dry Run" tone="secondary" type="submit" />
          </form>
          <form action={runPromotionChecksAction}>
            <input type="hidden" name="promotionId" value={promotion.id} />
            <Button label="Run Checks" tone="secondary" type="submit" />
          </form>
          <form action={promotionAction}>
            <input type="hidden" name="promotionId" value={promotion.id} />
            <input type="hidden" name="action" value="authorize" />
            <Button label="Authorize Promotion" tone="secondary" type="submit" />
          </form>
          <form action={promotionAction}>
            <input type="hidden" name="promotionId" value={promotion.id} />
            <input type="hidden" name="action" value="execute" />
            <Button label="Execute Promotion" tone="primary" type="submit" />
          </form>
        </div>
        <DataTable
          data={promotion.check_results}
          emptyMessage="No check results."
          columns={[
            { key: "name", header: "Check", render: (row) => row.name },
            { key: "state", header: "State", render: (row) => row.state },
            { key: "severity", header: "Severity", render: (row) => row.severity },
            { key: "detail", header: "Detail", render: (row) => row.detail },
            { key: "evidence", header: "Evidence", render: (row) => row.evidence },
            { key: "actor", header: "Evaluated By", render: (row) => row.evaluated_by },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="flex flex-wrap gap-2">
                  <form action={evaluatePromotionCheckAction}>
                    <input type="hidden" name="promotionId" value={promotion.id} />
                    <input type="hidden" name="checkId" value={row.id} />
                    <input type="hidden" name="state" value="passed" />
                    <Button label="Mark Passed" tone="secondary" type="submit" />
                  </form>
                  <form action={overridePromotionCheckAction}>
                    <input type="hidden" name="promotionId" value={promotion.id} />
                    <input type="hidden" name="checkId" value={row.id} />
                    <Button label="Override" tone="secondary" type="submit" />
                  </form>
                </div>
              )
            }
          ]}
        />
        <DataTable
          data={promotion.check_runs}
          emptyMessage="No queued check runs."
          columns={[
            { key: "scope", header: "Scope", render: (row) => row.scope },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "reason", header: "Trigger", render: (row) => row.trigger_reason },
            { key: "actor", header: "Enqueued By", render: (row) => row.enqueued_by },
            { key: "time", header: "Queued At", render: (row) => new Date(row.queued_at).toLocaleString() }
          ]}
        />
        <DataTable
          data={promotion.required_approvals}
          emptyMessage="No required approvals."
          columns={[
            { key: "reviewer", header: "Reviewer", render: (row) => row.reviewer },
            { key: "state", header: "State", render: (row) => row.state },
            { key: "scope", header: "Scope", render: (row) => row.scope },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <form action={overridePromotionApprovalAction} className="flex gap-2">
                  <input type="hidden" name="promotionId" value={promotion.id} />
                  <input type="hidden" name="reviewer" value={row.reviewer} />
                  <input
                    name="replacementReviewer"
                    defaultValue={row.reviewer}
                    className="w-40 rounded-md border border-chrome bg-white px-2 py-1 text-xs text-slate-700"
                  />
                  <Button label="Reassign" tone="secondary" type="submit" />
                </form>
              )
            }
          ]}
        />
        <DataTable
          data={promotion.overrides}
          emptyMessage="No overrides recorded."
          columns={[
            { key: "check", header: "Check", render: (row) => row.check_result_id },
            { key: "state", header: "State", render: (row) => row.state },
            { key: "reason", header: "Reason", render: (row) => row.reason },
            { key: "requested", header: "Requested By", render: (row) => row.requested_by },
            { key: "decided", header: "Decided By", render: (row) => row.decided_by },
            { key: "time", header: "Timestamp", render: (row) => new Date(row.created_at).toLocaleString() }
          ]}
        />
        <DataTable
          data={promotion.deployment_executions}
          emptyMessage="No deployment executions recorded."
          columns={[
            { key: "time", header: "Executed At", render: (row) => new Date(row.executed_at).toLocaleString() },
            { key: "target", header: "Target", render: (row) => row.target },
            { key: "integration", header: "Integration", render: (row) => row.integration_id },
            { key: "status", header: "Status", render: (row) => row.status },
            { key: "reference", header: "External Ref", render: (row) => row.external_reference ?? "None" },
            { key: "detail", header: "Detail", render: (row) => row.detail }
          ]}
        />
        <DataTable
          data={promotion.promotion_history}
          emptyMessage="No promotion history."
          columns={[
            { key: "time", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
            { key: "actor", header: "Actor", render: (row) => row.actor },
            { key: "action", header: "Action", render: (row) => row.action }
          ]}
        />
      </div>
    </PageShell>
  );
}
