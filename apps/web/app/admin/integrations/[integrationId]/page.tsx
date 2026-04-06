import { listIntegrationProjections, listIntegrationReconciliationLogs, listIntegrations } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../components/ui-helpers";
import {
  createIntegrationProjectionAction,
  deleteIntegrationAction,
  reconcileIntegrationAction,
  resolveIntegrationProjectionAction,
  syncIntegrationProjectionAction,
  updateIntegrationProjectionExternalStateAction,
  updateIntegrationAction
} from "../actions";

type IntegrationDetailPageProps = {
  params: Promise<{ integrationId: string }>;
};

export default async function AdminIntegrationDetailPage({ params }: IntegrationDetailPageProps) {
  const { integrationId } = await params;
  const integrations = await listIntegrations();
  const integration = integrations.find((item) => item.id === integrationId) ?? integrations[0];

  if (!integration) {
    return (
      <PageShell
        {...appShellProps("/admin/integrations", "Integration Detail", "The requested integration was not found.")}
        contextPanel={<a href="/admin/integrations" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Integrations</a>}
      >
        <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm text-sm text-slate-600">No integration available.</div>
      </PageShell>
    );
  }

  const [projections, reconciliationLogs] = await Promise.all([
    listIntegrationProjections(integration.id),
    listIntegrationReconciliationLogs(integration.id),
  ]);

  return (
    <PageShell
      {...appShellProps("/admin/integrations", `Integration: ${integration.name}`, "Edit or remove a managed integration from its dedicated drill-down page.")}
      contextPanel={
        <div className="space-y-4">
          <a href="/admin/integrations" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Integrations</a>
          <form action={deleteIntegrationAction}>
            <input type="hidden" name="integrationId" value={integration.id} />
            <Button label="Delete Integration" tone="secondary" type="submit" />
          </form>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="integrations"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" }
          ]}
        />
        <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Integration Settings" />
          <form action={updateIntegrationAction} className="mt-3 space-y-4">
            <input type="hidden" name="integrationId" value={integration.id} />
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Name</span><input name="name" defaultValue={integration.name} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Type</span><input name="type" defaultValue={integration.type} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Status</span><input name="status" defaultValue={integration.status} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Endpoint</span><input name="endpoint" defaultValue={integration.endpoint} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <SectionHeading title="Provider Settings" />
              <div className="mt-3 grid gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Provider</span><input name="provider" defaultValue={String(integration.settings?.provider ?? "")} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Base URL</span><input name="baseUrl" defaultValue={String(integration.settings?.base_url ?? "")} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Model</span><input name="model" defaultValue={String(integration.settings?.model ?? "")} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Workspace Id</span><input name="workspaceId" defaultValue={String(integration.settings?.workspace_id ?? "")} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <div className="space-y-2 md:col-span-2">
                  <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">API Key</span><input type="password" name="apiKey" placeholder={integration.has_api_key ? "Configured. Enter a new value to rotate." : "Provider API key"} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" autoComplete="new-password" /></label>
                  <label className="inline-flex items-center gap-2 text-xs text-slate-600"><input type="checkbox" name="clearApiKey" className="rounded border-chrome" />Clear stored API key</label>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Access Token</span><input type="password" name="accessToken" placeholder={integration.has_access_token ? "Configured. Enter a new value to rotate." : "OAuth/Bearer token for providers like Copilot"} className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" autoComplete="new-password" /></label>
                  <label className="inline-flex items-center gap-2 text-xs text-slate-600"><input type="checkbox" name="clearAccessToken" className="rounded border-chrome" />Clear stored access token</label>
                </div>
              </div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
              <div className="text-xs font-medium text-slate-500">Resolved Target</div>
              <div className="mt-2">{integration.resolved_endpoint ?? "N/A"}</div>
            </div>
            <div className="flex justify-end"><Button label="Save Integration" tone="primary" type="submit" /></div>
          </form>
        </div>
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
          <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
            <SectionHeading title="Projection Mappings" />
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-xs uppercase tracking-[0.16em] text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Entity</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">External Ref</th>
                    <th className="px-3 py-2">Last Sync</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {projections.length ? (
                    projections.map((projection) => (
                      <tr key={projection.id} className="align-top">
                        <td className="px-3 py-3 text-slate-700">
                          <div className="font-medium text-slate-900">{projection.entity_type}</div>
                          <div className="text-xs text-slate-500">{projection.entity_id}</div>
                          <div className="mt-1 text-xs text-slate-500">
                            Adapter {projection.adapter_type ?? "unknown"} via {projection.sync_source ?? "unspecified source"}
                          </div>
                          <div className="text-xs text-slate-500">
                            Capabilities {projection.adapter_capabilities.length ? projection.adapter_capabilities.join(", ") : "none declared"}
                          </div>
                          {projection.resolution_guidance ? (
                            <div className="mt-1 text-xs text-slate-500">
                              Resolution guidance: {projection.resolution_guidance}
                            </div>
                          ) : null}
                          {projection.conflicts.length ? (
                            <div className="mt-2 space-y-2">
                              <div className="rounded-lg border border-rose-200 bg-rose-50 px-2 py-2 text-xs text-rose-900">
                                {projection.conflicts.length} conflict{projection.conflicts.length === 1 ? "" : "s"} detected
                              </div>
                              {projection.conflicts.map((conflict, index) => (
                                <div key={`${projection.id}-${index}`} className="rounded-lg border border-rose-200 bg-rose-50 px-2 py-2 text-xs text-rose-900">
                                  <div className="font-medium">{String(conflict.field)}</div>
                                  <div>Canonical: {String(conflict.internal)}</div>
                                  <div>External: {String(conflict.external)}</div>
                                </div>
                              ))}
                            </div>
                          ) : null}
                        </td>
                        <td className="px-3 py-3 text-slate-700">{projection.projection_status}</td>
                        <td className="px-3 py-3 text-slate-700">{projection.external_ref ?? "Pending external ref"}</td>
                        <td className="px-3 py-3 text-slate-700">{projection.last_synced_at ? new Date(projection.last_synced_at).toLocaleString() : "Not synced"}</td>
                        <td className="px-3 py-3">
                          <div className="flex flex-col gap-2">
                            <form action={syncIntegrationProjectionAction}>
                              <input type="hidden" name="integrationId" value={integration.id} />
                              <input type="hidden" name="projectionId" value={projection.id} />
                              <Button label="Sync" tone="secondary" type="submit" />
                            </form>
                            <form action={updateIntegrationProjectionExternalStateAction} className="space-y-2 rounded-lg border border-chrome bg-slate-50 p-2">
                              <input type="hidden" name="integrationId" value={integration.id} />
                              <input type="hidden" name="projectionId" value={projection.id} />
                              <input name="externalStatus" placeholder="External status" className="w-full rounded border border-chrome bg-white px-2 py-1 text-xs text-slate-700" />
                              <input name="externalTitle" placeholder="External title" className="w-full rounded border border-chrome bg-white px-2 py-1 text-xs text-slate-700" />
                              <input name="externalRef" placeholder="External ref" className="w-full rounded border border-chrome bg-white px-2 py-1 text-xs text-slate-700" />
                              <Button label="Record External State" tone="secondary" type="submit" />
                            </form>
                            {projection.conflicts.length ? (
                              <form action={resolveIntegrationProjectionAction}>
                                <input type="hidden" name="integrationId" value={integration.id} />
                                <input type="hidden" name="projectionId" value={projection.id} />
                                <select
                                  name="action"
                                  defaultValue={projection.supported_resolution_actions[0] ?? "accept_internal"}
                                  className="mb-2 w-full rounded border border-chrome bg-white px-2 py-1 text-xs text-slate-700"
                                >
                                  {projection.supported_resolution_actions.map((action) => (
                                    <option key={`${projection.id}-${action}`} value={action}>
                                      {action}
                                    </option>
                                  ))}
                                </select>
                                <Button label="Resolve" tone="secondary" type="submit" />
                              </form>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-3 py-4 text-slate-600">
                        No projection mappings exist for this integration yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
              <SectionHeading title="Federation Controls" />
              <form action={createIntegrationProjectionAction} className="mt-3 space-y-3">
                <input type="hidden" name="integrationId" value={integration.id} />
                <label className="space-y-1 text-sm text-slate-700">
                  <span className="block text-xs font-medium text-slate-500">Entity Type</span>
                  <select name="entityType" defaultValue="request" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
                    <option value="request">request</option>
                    <option value="artifact">artifact</option>
                    <option value="change_set">change_set</option>
                    <option value="review">review</option>
                  </select>
                </label>
                <label className="space-y-1 text-sm text-slate-700">
                  <span className="block text-xs font-medium text-slate-500">Entity Id</span>
                  <input name="entityId" placeholder="req_001" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
                </label>
                <Button label="Create Projection" tone="secondary" type="submit" />
              </form>
              <form action={reconcileIntegrationAction} className="mt-3 border-t border-slate-200 pt-3">
                <input type="hidden" name="integrationId" value={integration.id} />
                <Button label="Run Reconciliation" tone="primary" type="submit" />
              </form>
            </div>
            <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
              <SectionHeading title="Reconciliation Activity" />
              <div className="mt-3 space-y-3">
                {reconciliationLogs.length ? (
                  reconciliationLogs.map((entry) => (
                    <div key={entry.id} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium text-slate-900">{entry.action}</div>
                        <div className="text-xs text-slate-500">{entry.created_at ? new Date(entry.created_at).toLocaleString() : "Timestamp unavailable"}</div>
                      </div>
                      <div className="mt-1 text-slate-600">{entry.detail ?? "No detail recorded."}</div>
                      <div className="mt-1 text-xs text-slate-500">Projection: {entry.projection_id}</div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    No reconciliation activity has been recorded for this integration.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
