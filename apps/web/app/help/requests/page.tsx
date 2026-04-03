import Link from "next/link";
import { PageShell } from "../../../components/ui-helpers";
import { HelpSection, HelpTabs, HelpTable, helpShellProps } from "../help-shared";

const requestPages = [
  { page: "Request List", route: "/requests", purpose: "Primary governed work list with filters and SLA risk visibility." },
  { page: "New Request", route: "/requests/new", purpose: "Template-first request intake flow for creating a draft request." },
  { page: "Request Detail", route: "/requests/[requestId]", purpose: "Canonical control plane for a single request, including actions, history, and related work." },
  { page: "Request Agents", route: "/requests/[requestId]/agents", purpose: "Agent assignment and session catalog for one request." },
  { page: "Agent Session", route: "/requests/[requestId]/agents/[sessionId]", purpose: "Interactive human-agent collaboration attached directly to the request." },
  { page: "Request History", route: "/requests/[requestId]/history", purpose: "Immutable timeline of request events and lineage." },
  { page: "Blocked Requests", route: "/requests/blocked", purpose: "Queue of requests blocked by checks, missing input, or governance conditions." },
  { page: "SLA Risk", route: "/requests/sla-risk", purpose: "Queue of requests with elevated policy-derived delivery risk." }
];

const requestFormFields = [
  { field: "Template", location: "Template picker", required: "Yes", meaning: "Determines the immutable intake schema, routing rules, and governance rules that will apply to the request." },
  { field: "Title", location: "New Request form", required: "Yes", meaning: "Short operational name for the work request. Appears in queues and drill-down pages." },
  { field: "Summary", location: "New Request form", required: "Yes", meaning: "Plain-language description of what governed work needs to happen." },
  { field: "Priority", location: "New Request form", required: "Yes", meaning: "Used for urgency and policy-derived SLA risk reporting." },
  { field: "Template-specific fields", location: "New Request form", required: "Depends on template", meaning: "Additional intake fields defined by the selected published template, including conditional requirements and enumerations." }
];

const requestActions = [
  { action: "Create Draft", when: "After completing intake", effect: "Creates the request in draft state and opens the request detail page." },
  { action: "Submit Request", when: "From request detail", effect: "Submits the request into the governed lifecycle using its bound template version." },
  { action: "Amend Request", when: "When approved by policy and workflow state", effect: "Changes the request through explicit governed mutation events rather than silent edits." },
  { action: "Clone / Cancel / Supersede", when: "From the request action surface", effect: "Supports controlled lineage operations for rework and replacement." },
  { action: "Assign to Agent", when: "From the request agents page", effect: "Starts an interactive agent session attached directly to the request." },
  { action: "Accept Response and Continue", when: "From a completed agent turn", effect: "Closes the current agent loop and allows the request to resume its workflow." }
];

export default function HelpRequestsPage() {
  return (
    <PageShell
      {...helpShellProps("Help: Requests", "Page-, form-, and field-level guidance for request intake, request detail, request actions, and agent collaboration.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Primary Mental Model</h2>
            <p className="mt-2 text-sm text-slate-600">
              The request is the root object. If you need to understand a piece of work, start from the request detail page and then drill down to runs, reviews, promotions, history, or agent sessions from there.
            </p>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Related Guides</h2>
            <div className="mt-2 grid gap-2 text-sm">
              <Link href="/help/journeys" className="text-accent hover:underline">Open request journeys</Link>
              <Link href="/help/operations" className="text-accent hover:underline">Open operations guide</Link>
            </div>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpTabs activeKey="requests" />
        <HelpSection title="Request Pages" description="These are the major request-related screens and what each one is for.">
          <HelpTable
            data={requestPages}
            columns={[
              { key: "page", header: "Page", render: (row) => row.page },
              { key: "route", header: "Route", render: (row) => row.route },
              { key: "purpose", header: "Purpose", render: (row) => row.purpose }
            ]}
          />
        </HelpSection>
        <HelpSection title="Create Request Form" description="Request creation starts with template selection. After a published template is chosen, the request form uses that template to render its intake fields.">
          <HelpTable
            data={requestFormFields}
            columns={[
              { key: "field", header: "Field", render: (row) => row.field },
              { key: "location", header: "Location", render: (row) => row.location },
              { key: "required", header: "Required", render: (row) => row.required },
              { key: "meaning", header: "Meaning", render: (row) => row.meaning }
            ]}
          />
        </HelpSection>
        <HelpSection title="Request Actions" description="The request detail and agent pages expose the main user actions that move governed work through the system.">
          <HelpTable
            data={requestActions}
            columns={[
              { key: "action", header: "Action", render: (row) => row.action },
              { key: "when", header: "When To Use It", render: (row) => row.when },
              { key: "effect", header: "Effect", render: (row) => row.effect }
            ]}
          />
        </HelpSection>
        <HelpSection title="Agent Collaboration" description="Agent sessions are attached to a request and persist transcript, status, and output. They are not free-floating chats.">
          <div className="grid gap-3 text-sm text-slate-700">
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Open the request and move to the <strong>Agents</strong> page for that request.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Choose the agent integration, provide an agent label and an initial prompt, and start the session.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">Use the session drill-down page to review the current state, latest agent response, and prior human guidance.</div>
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">When the response is satisfactory, use <strong>Accept Response and Continue</strong> so the request can resume its workflow.</div>
          </div>
        </HelpSection>
      </div>
    </PageShell>
  );
}
