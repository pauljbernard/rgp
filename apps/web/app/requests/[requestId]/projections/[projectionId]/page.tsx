import { getRequest, listRequestProjections } from "@/lib/server-api";
import Link from "next/link";
import { Badge, Button, KeyValueGrid, PageShell, SectionHeading, Tabs, appShellProps, statusTone } from "../../../../../components/ui-helpers";
import {
  resolveRequestProjectionAction,
  syncRequestProjectionAction,
  updateRequestProjectionExternalStateAction,
} from "./actions";

export default async function RequestProjectionPage({
  params,
}: {
  params: Promise<{ requestId: string; projectionId: string }>;
}) {
  const { requestId, projectionId } = await params;
  const [requestDetail, projections] = await Promise.all([getRequest(requestId), listRequestProjections(requestId)]);
  const projection = projections.find((item) => item.id === projectionId);

  if (!projection) {
    return (
      <PageShell {...appShellProps("/requests", "Projection Detail", "Federated projection drilldown for request-scoped remediation.")}>
        <div className="rounded-lg border border-chrome bg-panel p-5 shadow-panel text-sm text-slate-700">
          Projection not found for this request.
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell
      {...appShellProps("/requests", "Projection Detail", "Request-scoped federated projection drilldown with sync and remediation controls.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Request Context" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div className="font-medium">{requestDetail.request.title}</div>
            <div className="mt-1 text-slate-600">{requestDetail.request.summary}</div>
            <div className="mt-2 text-xs text-slate-500">
              {requestDetail.request.template_id}@{requestDetail.request.template_version} · {requestDetail.request.status}
            </div>
          </div>
          <SectionHeading title="Lineage" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-xs text-slate-600">
            request:{requestId} -&gt; projection:{projection.id} -&gt; external:{projection.external_system}
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="projection"
          tabs={[
            { key: "overview", label: "Overview", href: `/requests/${requestId}` },
            { key: "history", label: "History", href: `/requests/${requestId}/history` },
            { key: "projection", label: "Projection", href: `/requests/${requestId}/projections/${projection.id}` },
          ]}
        />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <SectionHeading title="Projection Overview" />
            <KeyValueGrid
              items={[
                { label: "External System", value: projection.external_system },
                { label: "External Ref", value: projection.external_ref ?? "None recorded" },
                { label: "Projection Status", value: <Badge tone={projection.conflicts.length ? "warning" : statusTone("completed")}>{projection.projection_status}</Badge> },
                { label: "Adapter", value: projection.adapter_type ?? "unknown" },
                { label: "Sync Source", value: projection.sync_source ?? "unspecified" },
                { label: "Capabilities", value: projection.adapter_capabilities.length ? projection.adapter_capabilities.join(", ") : "none declared" },
                { label: "Last Projected", value: projection.last_projected_at ? new Date(projection.last_projected_at).toLocaleString() : "Never" },
                { label: "Last Synced", value: projection.last_synced_at ? new Date(projection.last_synced_at).toLocaleString() : "Never" },
              ]}
            />
            <SectionHeading title="Conflict Detail" />
            <div className="space-y-2">
              {projection.conflicts.length ? (
                projection.conflicts.map((conflict) => (
                  <div key={`${projection.id}-${String(conflict.field)}`} className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                    <div className="font-medium">{String(conflict.field)}</div>
                    <div>canonical: {String(conflict.internal)}</div>
                    <div>external: {String(conflict.external)}</div>
                  </div>
                ))
              ) : (
                <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  No active conflicts are recorded for this projection.
                </div>
              )}
            </div>
            <SectionHeading title="External State" />
            <pre className="overflow-x-auto rounded-lg border border-chrome bg-slate-50 p-4 text-xs text-slate-700">
              {JSON.stringify(projection.external_state ?? {}, null, 2)}
            </pre>
          </div>
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <SectionHeading title="Remediation Controls" />
            <form action={syncRequestProjectionAction}>
              <input type="hidden" name="requestId" value={requestId} />
              <input type="hidden" name="projectionId" value={projection.id} />
              <Button label="Sync Projection" tone="secondary" type="submit" />
            </form>
            <form action={updateRequestProjectionExternalStateAction} className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-4">
              <input type="hidden" name="requestId" value={requestId} />
              <input type="hidden" name="projectionId" value={projection.id} />
              <div className="text-sm font-medium text-slate-700">Record External State</div>
              <input name="externalStatus" placeholder="External status" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" />
              <input name="externalTitle" placeholder="External title" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" />
              <input name="externalRef" placeholder="External reference" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" />
              <Button label="Save External State" tone="secondary" type="submit" />
            </form>
            <form action={resolveRequestProjectionAction} className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-4">
              <input type="hidden" name="requestId" value={requestId} />
              <input type="hidden" name="projectionId" value={projection.id} />
              <div className="text-sm font-medium text-slate-700">Resolve Projection</div>
              <select name="action" defaultValue={projection.supported_resolution_actions[0] ?? "accept_internal"} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700">
                {projection.supported_resolution_actions.map((action) => (
                  <option key={action} value={action}>
                    {action}
                  </option>
                ))}
              </select>
              <div className="text-xs text-slate-500">
                {projection.resolution_guidance ?? "No substrate-specific guidance is available."}
              </div>
              <Button label="Apply Resolution" tone="primary" type="submit" />
            </form>
            <Link href={`/admin/integrations/${projection.integration_id}`} className="block text-sm text-accent">
              Open integration drilldown
            </Link>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
