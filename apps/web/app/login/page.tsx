import { Button, PageShell, SectionHeading, appShellProps } from "../../components/ui-helpers";
import Link from "next/link";
import { loginWithPasswordAction, logoutAction } from "./actions";

const profiles = [
  {
    id: "admin",
    title: "Platform Admin",
    description: "Cross-tenant administration plus operator, reviewer, and submitter workflows.",
  },
  {
    id: "reviewer",
    title: "Reviewer",
    description: "Review-focused access on tenant_demo with no operator authority.",
  },
  {
    id: "submitter",
    title: "Submitter",
    description: "Intake-focused access on tenant_demo for request creation and submission.",
  },
  {
    id: "observer",
    title: "Observer",
    description: "Read-only tenant_demo session for audit and verification walkthroughs.",
  },
  {
    id: "other_admin",
    title: "Other Tenant Admin",
    description: "Tenant-scoped administration for tenant_other to verify isolation behavior.",
  },
];

const errorMessages: Record<string, string> = {
  state_mismatch: "The authorization callback state did not validate. Start the sign-in flow again.",
  exchange_failed: "The authorization code exchange failed. Start the sign-in flow again.",
};

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const errorMessage = params.error ? errorMessages[params.error] ?? "The sign-in flow failed." : null;

  return (
    <PageShell
      {...appShellProps("/login", "Login", "Development authorization entry using redirect and callback exchange.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Session Notes" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            This login flow uses an authorization redirect and callback exchange path. The resulting bearer token is stored in an httpOnly session cookie.
          </div>
          <form action={logoutAction}>
            <Button label="Clear Session" tone="secondary" type="submit" />
          </form>
        </div>
      }
    >
      <div className="max-w-3xl space-y-4 rounded-xl border border-chrome bg-panel p-6 shadow-panel">
        <div>
          <div className="text-xs font-medium text-slate-500">Authentication</div>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">Start Development Session</h2>
        </div>
        {errorMessage ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{errorMessage}</div>
        ) : null}
        <div className="grid gap-3">
          {profiles.map((profile) => (
            <a
              key={profile.id}
              href={`/login/start?profile=${profile.id}`}
              className="rounded-xl border border-chrome bg-slate-50 px-4 py-4 text-left transition hover:border-slate-400 hover:bg-white"
            >
              <div className="text-sm font-semibold text-slate-900">{profile.title}</div>
              <div className="mt-1 text-sm text-slate-600">{profile.description}</div>
            </a>
          ))}
        </div>
        <div className="rounded-xl border border-chrome bg-white px-4 py-4">
          <div className="text-sm font-semibold text-slate-900">Local Credentials</div>
          <p className="mt-1 text-sm text-slate-600">Use a provisioned user account when local credential login is enabled for this environment.</p>
          <form action={loginWithPasswordAction} className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="grid gap-1 text-sm text-slate-700">
              <span className="text-xs font-medium text-slate-500">Email</span>
              <input name="email" type="email" className="rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" placeholder="user@example.com" />
            </label>
            <label className="grid gap-1 text-sm text-slate-700">
              <span className="text-xs font-medium text-slate-500">Password</span>
              <input name="password" type="password" className="rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" autoComplete="current-password" />
            </label>
            <label className="grid gap-1 text-sm text-slate-700">
              <span className="text-xs font-medium text-slate-500">Tenant</span>
              <input name="tenantId" defaultValue="tenant_demo" className="rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700" />
            </label>
            <div className="md:col-span-3 flex items-center justify-between gap-3">
              <Button label="Sign In with Password" tone="primary" type="submit" />
              <Link href="/register" className="text-sm font-medium text-accent hover:underline">Create account request</Link>
            </div>
          </form>
        </div>
        <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Use the tenant_other profile to validate tenant-isolated templates, policies, integrations, and capabilities.
        </div>
      </div>
    </PageShell>
  );
}
