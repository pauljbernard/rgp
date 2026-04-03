import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../components/ui-helpers";
import { createIntegrationAction } from "../actions";

export default function AdminNewIntegrationPage() {
  return (
    <PageShell
      {...appShellProps("/admin/integrations", "Create Integration", "Create a new managed integration and then maintain it from its drill-down page.")}
      contextPanel={<a href="/admin/integrations" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">Back to Integrations</a>}
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
          <SectionHeading title="Create Integration" />
          <form action={createIntegrationAction} className="mt-3 space-y-4">
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Integration Id</span><input name="id" placeholder="int_004" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Name</span><input name="name" placeholder="Slack Notifications" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Type</span><input name="type" placeholder="notification" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Status</span><input name="status" defaultValue="connected" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Endpoint</span><input name="endpoint" placeholder="slack://ops-alerts" className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <SectionHeading title="Provider Settings" />
              <div className="mt-3 grid gap-4 md:grid-cols-2">
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Provider</span><input name="provider" placeholder="openai | anthropic | microsoft" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Base URL</span><input name="baseUrl" placeholder="https://api.openai.com/v1" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Model</span><input name="model" placeholder="gpt-5.4" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Workspace Id</span><input name="workspaceId" placeholder="Optional workspace or tenant scope" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" /></label>
                <label className="space-y-1 text-sm text-slate-700 md:col-span-2"><span className="block text-xs font-medium text-slate-500">API Key</span><input type="password" name="apiKey" placeholder="Provider API key" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" autoComplete="new-password" /></label>
                <label className="space-y-1 text-sm text-slate-700 md:col-span-2"><span className="block text-xs font-medium text-slate-500">Access Token</span><input type="password" name="accessToken" placeholder="OAuth/Bearer token for providers like Copilot" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700" autoComplete="new-password" /></label>
              </div>
            </div>
            <div className="flex justify-end"><Button label="Create Integration" tone="primary" type="submit" /></div>
          </form>
        </div>
      </div>
    </PageShell>
  );
}
