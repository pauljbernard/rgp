import { PageShell } from "../../../components/ui-helpers";
import { HelpSection, HelpTabs, HelpTable, helpShellProps } from "../help-shared";

const operationsAreas = [
  { area: "Runs", route: "/runs", use: "Monitor active, queued, failed, and completed execution instances." },
  { area: "Failed Runs", route: "/runs/failed", use: "Investigate execution failures and decide on retry or cancellation." },
  { area: "Review Queue", route: "/reviews/queue", use: "Reviewer worklist for approve, reject, request changes, or reassignment actions." },
  { area: "Promotions Pending", route: "/promotions/pending", use: "Queue of requests that have passed review and are waiting on promotion checks or approval." },
  { area: "Blocked Requests", route: "/requests/blocked", use: "Identify requests that need explicit human or authoring intervention." },
  { area: "SLA Risk", route: "/requests/sla-risk", use: "Inspect requests that policy logic currently marks as elevated delivery risk." }
];

const operationalDecisions = [
  { decision: "Run retry or diagnosis", source: "Failed Runs", notes: "Use when execution failed and work cannot continue without operator intervention." },
  { decision: "Review approve/reject/request changes", source: "Review Queue", notes: "Use when human governance review is required before work can advance." },
  { decision: "Promotion approval", source: "Promotion Pending or Promotion Detail", notes: "Use when governed work is ready for final approval and deployment execution." },
  { decision: "Resolve blockers", source: "Blocked Requests", notes: "Use when requests are waiting on missing input, failed checks, or invalid configuration." }
];

export default function HelpOperationsPage() {
  return (
    <PageShell
      {...helpShellProps("Help: Operations", "Guidance for queues, runs, reviews, promotions, and the operational decision points that move work forward.")}
      contextPanel={
        <div className="space-y-5 text-sm text-slate-600">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Queue Rule</h2>
            <p className="mt-2">
              Operational work starts from queue pages. Queues are table-driven, filterable, and actionable. Use the queue first, then drill into the specific governed object.
            </p>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpTabs activeKey="operations" />
        <HelpSection title="Operational Areas" description="These are the core operator and reviewer surfaces inside the application.">
          <HelpTable
            data={operationsAreas}
            columns={[
              { key: "area", header: "Area", render: (row) => row.area },
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "use", header: "Use", render: (row) => row.use }
            ]}
          />
        </HelpSection>
        <HelpSection title="Operational Decision Points" description="These are the explicit human decisions the system expects rather than hiding behind background automation.">
          <HelpTable
            data={operationalDecisions}
            columns={[
              { key: "decision", header: "Decision", render: (row) => row.decision },
              { key: "source", header: "Primary Source", render: (row) => row.source },
              { key: "notes", header: "Notes", render: (row) => row.notes }
            ]}
          />
        </HelpSection>
        <HelpSection title="What To Check When Work Is Stuck" description="Start from the request and then inspect the relevant operational queue or drill-down page.">
          <div className="grid gap-3 text-sm text-slate-700">
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Check whether the request has active or failed checks blocking transition.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Check whether the request is waiting in the review queue or promotion queue.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Check whether an agent session is still open and waiting on human input.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use the request history page to understand the exact event sequence that led to the current state.</div>
          </div>
        </HelpSection>
      </div>
    </PageShell>
  );
}
