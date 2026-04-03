import Link from "next/link";
import { PageShell } from "../../components/ui-helpers";
import { HelpSection, HelpTabs, HelpTable, helpShellProps } from "./help-shared";

const guideAreas = [
  {
    area: "Requests",
    purpose: "Create, submit, monitor, amend, clone, cancel, supersede, and complete governed work.",
    entry: "/requests",
    help: "/help/requests"
  },
  {
    area: "Operations",
    purpose: "Work queues for runs, reviews, promotions, blocked requests, and SLA risk.",
    entry: "/runs",
    help: "/help/operations"
  },
  {
    area: "Admin",
    purpose: "Manage templates, organization records, integrations, and policies.",
    entry: "/admin/templates",
    help: "/help/admin"
  },
  {
    area: "Analytics",
    purpose: "Inspect delivery, workflow, performance, cost, and portfolio reporting.",
    entry: "/analytics",
    help: "/help/analytics"
  },
  {
    area: "Journeys",
    purpose: "Understand the supported end-to-end user journeys and how work moves through the platform.",
    entry: "/help/journeys",
    help: "/help/journeys"
  }
];

const principles = [
  "Start from list pages. Lists are the canonical entry point into the system.",
  "Use the request as the primary source of truth for a unit of governed work.",
  "Treat agent interaction as governed request collaboration, not as a detached chat session.",
  "Expect reviews, approvals, and promotions to remain explicit rather than automatic or hidden.",
  "Use analytics for operational insight, but rely on the request lineage for authoritative evidence."
];

export default function HelpOverviewPage() {
  return (
    <PageShell
      {...helpShellProps("Help and User Guide", "Authenticated in-application documentation covering pages, forms, fields, and supported user journeys.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">How To Use This Guide</h2>
            <p className="mt-2 text-sm text-slate-600">
              Start with the section that matches your task. Use the Requests guide for day-to-day work, Operations for governed queues, Admin for configuration and catalog management, Analytics for reporting, and Journeys for end-to-end flows.
            </p>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Audience</h2>
            <div className="mt-2 grid gap-2 text-sm text-slate-600">
              <div>Submitters: request intake, status tracking, and agent collaboration.</div>
              <div>Reviewers and operators: queues, decisions, and workflow progression.</div>
              <div>Admins: templates, organization, integrations, and policies.</div>
              <div>Executives and leads: analytics, trends, and portfolio reporting.</div>
            </div>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpTabs activeKey="overview" />
        <HelpSection title="Platform Model" description="RGP is a governed work system. The request is the authoritative unit of work, and the rest of the application exists to route, execute, review, promote, and analyze requests under explicit governance.">
          <div className="grid gap-2 text-sm text-slate-700">
            {principles.map((item) => (
              <div key={item} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">
                {item}
              </div>
            ))}
          </div>
        </HelpSection>
        <HelpSection title="Guide Map" description="Use this table to navigate to the right help topic for the task you are performing.">
          <HelpTable
            data={guideAreas}
            columns={[
              { key: "area", header: "Guide Area", render: (row) => row.area },
              { key: "purpose", header: "Purpose", render: (row) => row.purpose },
              {
                key: "entry",
                header: "Primary App Entry",
                render: (row) => (
                  <Link href={row.entry} className="font-medium text-accent hover:underline">
                    {row.entry}
                  </Link>
                )
              },
              {
                key: "help",
                header: "Open Guide",
                render: (row) => (
                  <Link href={row.help} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                    Open
                  </Link>
                )
              }
            ]}
          />
        </HelpSection>
        <HelpSection title="Supported User Journey Families" description="The application supports several major journey families, each of which is documented in detail in the Journeys section.">
          <HelpTable
            data={[
              { journey: "Request Intake", summary: "Choose a published template, create a draft, submit it, and monitor progress.", href: "/help/journeys" },
              { journey: "Agent-Assisted Work", summary: "Assign a request to an agent integration, collaborate across turns, accept the result, and resume the workflow.", href: "/help/journeys" },
              { journey: "Review and Promotion", summary: "Advance governed work through review queues, promotion approval, deployment, and completion.", href: "/help/journeys" },
              { journey: "Administration", summary: "Manage templates, organization, integrations, and policies from catalog-first admin screens.", href: "/help/admin" },
              { journey: "Analytics", summary: "Use filterable operational reporting and time-series analytics across delivery, performance, cost, and portfolio scopes.", href: "/help/analytics" }
            ]}
            columns={[
              { key: "journey", header: "Journey", render: (row) => row.journey },
              { key: "summary", header: "Summary", render: (row) => row.summary },
              {
                key: "guide",
                header: "Guide",
                render: (row) => (
                  <Link href={row.href} className="font-medium text-accent hover:underline">
                    Open Guide
                  </Link>
                )
              }
            ]}
          />
        </HelpSection>
      </div>
    </PageShell>
  );
}
