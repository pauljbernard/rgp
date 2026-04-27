import { render, screen } from "@testing-library/react";
import NewRequestPage from "./page";

vi.mock("@/lib/server-api", () => ({
  listNodes: vi.fn(async () => [
    {
      id: "node_demo_001",
      tenant_id: "tenant_demo",
      name: "Paul Local SBCL Agent",
      operator_id: "operator_demo_001",
      operator_type: "individual",
      employment_model: "employee",
      owner_user_id: "user_demo",
      team_id: "team_assessment_quality",
      environment_id: "env_local_demo",
      runtime_kind: "sbcl-agent",
      version: "0.1.0",
      status: "online",
      trust_tier: "standard",
      health_state: "healthy",
      current_load: 1,
      drain_state: "active",
      heartbeat_age_seconds: 15,
      liveness_state: "healthy",
      readiness_state: "ready",
      readiness_reason: "Node is healthy and accepting work.",
      active_assignment_count: 0,
      active_execution_count: 0,
      blocked_assignment_count: 0,
      visibility_profile: "standard",
      billing_profile: "organization_funded",
      routing_tags: ["lisp", "governed"],
      capabilities: [],
      last_seen_at: "2026-04-18T12:00:00Z",
      workspace_identity: "/Volumes/data/development/rgp",
      repo_identity: "pauljbernard/rgp",
      metadata: {},
      created_at: "2026-04-18T11:30:00Z",
      updated_at: "2026-04-18T12:00:00Z"
    }
  ]),
  listTemplates: vi.fn(async () => [
    {
      id: "tmpl_assessment",
      version: "1.4.0",
      name: "Assessment Revision",
      description: "Governed assessment revision requests.",
      status: "published",
      schema: {
        required: ["assessment_id", "revision_reason"],
        properties: {
          assessment_id: { title: "Assessment ID" },
          revision_reason: {
            title: "Revision Reason",
            enum: ["Standards alignment", "Quality remediation"]
          }
        }
      }
    },
    {
      id: "tmpl_curriculum",
      version: "3.2.0",
      name: "Curriculum Change",
      description: "Governed curriculum changes.",
      status: "published",
      schema: { required: [], properties: {} }
    }
  ])
}));

describe("NewRequestPage", () => {
  it("requires explicit template selection before showing the form", async () => {
    const ui = await NewRequestPage({
      searchParams: Promise.resolve({})
    });
    render(ui);

    expect(screen.getByRole("heading", { name: "Select Request Template" })).toBeInTheDocument();
    expect(screen.getByLabelText("Search Templates")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /^Template ▲$/ })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /^Template ID ↕$/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Assessment Revision" })).toHaveAttribute("href", "/requests/new?template=tmpl_assessment%401.4.0");
    expect(screen.getByRole("link", { name: "Close" })).toHaveAttribute("href", "/requests");
    expect(screen.getByText("Page 1 of 1 · 2 total records")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Create Draft" })).not.toBeInTheDocument();
  });

  it("shows the request form only after a template is chosen", async () => {
    const ui = await NewRequestPage({
      searchParams: Promise.resolve({ template: "tmpl_assessment@1.4.0" })
    });
    render(ui);

    expect(screen.getByText("Selected Template")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Draft" })).toBeInTheDocument();
    expect(screen.getByLabelText("Execution Mode")).toBeInTheDocument();
    expect(screen.getByLabelText("Assigned Node")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Paul Local SBCL Agent (online)" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Choose Different Template" })).toHaveAttribute(
      "href",
      "/requests/new?template=tmpl_assessment%401.4.0&choose_template=1",
    );
  });

  it("keeps the template picker open with an error banner during recovery", async () => {
    const ui = await NewRequestPage({
      searchParams: Promise.resolve({
        template: "tmpl_assessment@1.4.0",
        choose_template: "1",
        error: "Request creation failed",
        template_query: "curriculum"
      })
    });
    render(ui);

    expect(screen.getByText("Request creation failed")).toBeInTheDocument();
    expect(screen.getByDisplayValue("curriculum")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Curriculum Change" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Assessment Revision" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Form" })).toHaveAttribute(
      "href",
      "/requests/new?template=tmpl_assessment%401.4.0"
    );
  });
});
