import { PageShell } from "../../../components/ui-helpers";
import { HelpSection, HelpTabs, HelpTable, helpShellProps } from "../help-shared";

const journeys = [
  {
    journey: "Create and Submit a Request",
    users: "Submitter",
    steps: "Open Requests, choose New, select a published template, complete the intake form, create a draft, then submit from the request detail page."
  },
  {
    journey: "Agent-Assisted Request",
    users: "Submitter or operator",
    steps: "Open the request agents page, assign an agent integration, collaborate across turns, review the agent response, and accept the response so the request can continue."
  },
  {
    journey: "Review and Approval",
    users: "Reviewer",
    steps: "Open the review queue, open the request or review item, then approve, reject, request changes, or use governed reassignment when available."
  },
  {
    journey: "Promotion and Completion",
    users: "Operator or approver",
    steps: "Open Promotion Pending, inspect promotion readiness, perform the approval action, execute promotion, and confirm completion state."
  },
  {
    journey: "Template Authoring",
    users: "Admin",
    steps: "Open Admin Templates, select a version, author or validate a draft, compare it, then publish or deprecate it when governance conditions are satisfied."
  },
  {
    journey: "Organization and Integration Administration",
    users: "Admin",
    steps: "Use Admin Organization and Admin Integrations to manage teams, users, memberships, portfolios, and managed provider settings."
  },
  {
    journey: "Analytics Review",
    users: "Executive, lead, operator, admin",
    steps: "Open Analytics, choose the reporting family, apply scope filters, inspect charts and tables, then drill back into the operational object that explains the reported trend."
  }
];

export default function HelpJourneysPage() {
  return (
    <PageShell
      {...helpShellProps("Help: User Journeys", "End-to-end user journeys supported by the application and how to complete them inside the authenticated product.")}
      contextPanel={
        <div className="space-y-5 text-sm text-slate-600">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Journey Rule</h2>
            <p className="mt-2">
              Journeys start from a list or queue, move into a detail page, then drill into sub-detail pages only when needed. This keeps navigation aligned with the table-first IA.
            </p>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpTabs activeKey="journeys" />
        <HelpSection title="Supported User Journeys" description="These are the primary workflow paths the current application supports for logged-in users.">
          <HelpTable
            data={journeys}
            columns={[
              { key: "journey", header: "Journey", render: (row) => row.journey },
              { key: "users", header: "Typical User", render: (row) => row.users },
              { key: "steps", header: "How It Works", render: (row) => row.steps }
            ]}
          />
        </HelpSection>
        <HelpSection title="What Counts as Completion" description="Most journeys end with an explicit, visible outcome. RGP avoids hidden completion.">
          <div className="grid gap-3 text-sm text-slate-700">
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">A request intake journey is complete when the request is created, submitted, and visible in the governed lifecycle.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">An agent journey is complete when the session has produced a satisfactory response and the user has accepted that response to resume the request workflow.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">A review journey is complete when the review decision is recorded explicitly.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">A promotion journey is complete when promotion approval, execution, and final completion evidence are present.</div>
          </div>
        </HelpSection>
      </div>
    </PageShell>
  );
}
