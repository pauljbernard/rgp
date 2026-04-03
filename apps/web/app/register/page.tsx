import Link from "next/link";
import { listPublicRegistrationOptions } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, appShellProps } from "../../components/ui-helpers";
import { submitRegistrationAction } from "./actions";

export default async function RegisterPage({
  searchParams,
}: {
  searchParams: Promise<{ submitted?: string; error?: string }>;
}) {
  const params = await searchParams;
  const options = await listPublicRegistrationOptions();
  const selectedTenantId = options.tenants[0]?.id ?? "tenant_demo";
  const selectedOrganizationId = options.organizations[0]?.id ?? "";

  return (
    <PageShell
      {...appShellProps("/register", "Request an Account", "Create a governed user-registration request for administrative review.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="What Happens Next" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Registration requests are routed as governed work. An administrator reviews the request, approves or rejects it, and then provisions account access.
          </div>
          <Link href="/login" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">
            Back to Login
          </Link>
        </div>
      }
    >
      <div className="max-w-3xl space-y-4 rounded-xl border border-chrome bg-panel p-6 shadow-panel">
        <div>
          <div className="text-xs font-medium text-slate-500">Registration</div>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">Create Account Request</h2>
        </div>
        {params.submitted ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">Your registration request was submitted for administrative review.</div> : null}
        {params.error ? <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">The registration request could not be submitted. Review the form and try again.</div> : null}
        <form action={submitRegistrationAction} className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Full Name</span><input name="displayName" required className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
          <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Email</span><input name="email" type="email" required className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
          <label className="space-y-1 text-sm text-slate-700">
            <span className="block text-xs font-medium text-slate-500">Tenant</span>
            <select name="tenantId" defaultValue={selectedTenantId} required className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
              {options.tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>{tenant.name}</option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-sm text-slate-700">
            <span className="block text-xs font-medium text-slate-500">Organization</span>
            <select name="organizationId" defaultValue={selectedOrganizationId} required className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
              {options.organizations.map((organization) => (
                <option key={organization.id} value={organization.id}>{organization.name}</option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-sm text-slate-700"><span className="block text-xs font-medium text-slate-500">Job Title</span><input name="jobTitle" required className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
          <label className="space-y-1 text-sm text-slate-700">
            <span className="block text-xs font-medium text-slate-500">Requested Team</span>
            <select name="requestedTeamId" required className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700">
              <option value="">Select a team</option>
              {options.organizations.map((organization) => (
                <optgroup key={organization.id} label={organization.name}>
                  {options.teams
                    .filter((team) => team.organization_id === organization.id)
                    .map((team) => (
                      <option key={team.id} value={team.id}>{team.name} ({team.kind})</option>
                    ))}
                </optgroup>
              ))}
            </select>
          </label>
          <fieldset className="space-y-2 text-sm text-slate-700 md:col-span-2">
            <legend className="text-xs font-medium text-slate-500">Requested Access</legend>
            <label className="flex items-center gap-2"><input type="checkbox" name="requestedRoles" value="submitter" defaultChecked /> Submitter</label>
            <label className="flex items-center gap-2"><input type="checkbox" name="requestedRoles" value="reviewer" /> Reviewer</label>
            <label className="flex items-center gap-2"><input type="checkbox" name="requestedRoles" value="operator" /> Operator</label>
          </fieldset>
          <label className="space-y-1 text-sm text-slate-700 md:col-span-2"><span className="block text-xs font-medium text-slate-500">Business Justification</span><textarea name="businessJustification" required className="min-h-28 w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" /></label>
          <div className="md:col-span-2 flex justify-end">
            <Button label="Submit Registration Request" tone="primary" type="submit" />
          </div>
        </form>
      </div>
    </PageShell>
  );
}
