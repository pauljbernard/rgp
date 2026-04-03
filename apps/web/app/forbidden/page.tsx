import Link from "next/link";
import { PageShell, SectionHeading, appShellProps } from "../../components/ui-helpers";

type ForbiddenPageProps = {
  searchParams?: Promise<{
    from?: string;
  }>;
};

export default async function ForbiddenPage({ searchParams }: ForbiddenPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const from = resolvedSearchParams.from ? decodeURIComponent(resolvedSearchParams.from) : undefined;

  return (
    <PageShell
      {...appShellProps(
        "/forbidden",
        "Access Restricted",
        "Your current signed-in role does not have access to this page or API surface."
      )}
      contextPanel={
        <div className="space-y-4">
          <div>
            <SectionHeading title="Next Steps" />
            <p className="mt-2 text-sm text-slate-600">
              Use a platform-admin profile for admin-only pages, or return to a workflow page that is available to your current role.
            </p>
          </div>
          <div className="space-y-2 text-sm">
            <Link className="block rounded-lg border border-chrome px-3 py-2 font-medium text-slate-700" href="/requests">
              Return to Requests
            </Link>
            <Link className="block rounded-lg border border-chrome px-3 py-2 font-medium text-slate-700" href="/login">
              Switch Profile
            </Link>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4">
          <h2 className="text-lg font-semibold text-amber-950">This route requires additional permissions.</h2>
          <p className="mt-2 text-sm text-amber-900">
            The application blocked the request instead of failing open. Sign in with a role that has access to this surface if you need to continue.
          </p>
        </div>
        {from ? (
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Attempted route: <span className="font-mono text-xs">{from}</span>
          </div>
        ) : null}
      </div>
    </PageShell>
  );
}
