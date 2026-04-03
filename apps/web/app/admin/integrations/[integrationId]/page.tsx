import { listIntegrations } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../components/ui-helpers";
import { deleteIntegrationAction, updateIntegrationAction } from "../actions";

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
      </div>
    </PageShell>
  );
}
