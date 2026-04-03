import { render, screen } from "@testing-library/react";
import React from "react";
import AdminTemplatesPage from "./page";

vi.mock("next/link", () => ({
  default: ({ href, children, prefetch: _prefetch, ...props }: { href: string; children: React.ReactNode; prefetch?: boolean }) => (
    <a href={href} {...props}>
      {children}
    </a>
  )
}));

vi.mock("@/lib/server-api", () => ({
  listAdminTemplates: vi.fn(async () => [
    {
      id: "tmpl_curriculum",
      version: "3.2.0",
      name: "Curriculum Generation",
      description: "Generates a governed instructional unit.",
      status: "draft",
      schema: {
        required: ["subject"],
        properties: {
          subject: { type: "string", title: "Subject Area", order: 1, enum: ["Math", "Science"] },
          grade_level: { type: "string", title: "Grade Level", order: 2 }
        },
        routing: {
          owner_team: "team_curriculum_science",
          reviewers: ["reviewer_nina"],
          owner_team_by_field: {
            subject: {
              Science: { order: 1, value: "team_curriculum_science" }
            }
          }
        },
        conditional_required: [
          {
            order: 1,
            when: { field: "subject", equals: "Science" },
            field: "grade_level",
            message: "Science requires grade level."
          }
        ],
        expected_artifact_types: ["doc"],
        check_requirements: ["policy_pack"],
        promotion_requirements: ["approval:ops"]
      },
      created_at: "2026-04-01T10:00:00Z",
      updated_at: "2026-04-01T10:00:00Z"
    },
    {
      id: "tmpl_curriculum",
      version: "3.1.0",
      name: "Curriculum Generation",
      description: "Previous version.",
      status: "published",
      schema: {
        required: ["subject"],
        properties: {
          subject: { type: "string", title: "Subject", order: 1 }
        },
        routing: {},
        conditional_required: [],
        expected_artifact_types: [],
        check_requirements: [],
        promotion_requirements: []
      },
      created_at: "2026-03-31T10:00:00Z",
      updated_at: "2026-03-31T10:00:00Z"
    }
  ]),
  validateAdminTemplateDefinition: vi.fn(async () => ({
    valid: true,
    issues: [],
    preview: {
      field_count: 2,
      required_fields: ["subject"],
      conditional_rule_count: 1,
      routing_rule_count: 1,
      artifact_type_count: 1,
      check_requirement_count: 1,
      promotion_requirement_count: 1,
      routed_fields: ["subject"],
      fields: [
        { key: "subject", title: "Subject", field_type: "string", required: true, enum_values: ["Math", "Science"] },
        { key: "grade_level", title: "Grade Level", field_type: "string", required: false, enum_values: [] }
      ]
    }
  }))
}));

describe("AdminTemplatesPage", () => {
  it("renders the template workbench with creation, validation, comparison, and delete controls", async () => {
    const ui = await AdminTemplatesPage({
      params: Promise.resolve({ templateId: "tmpl_curriculum", version: "3.2.0" }),
      searchParams: Promise.resolve({ template: "tmpl_curriculum", version: "3.2.0", validate: "1" })
    });
    render(ui);

    expect(screen.getByRole("heading", { name: "Selected Version" })).toBeInTheDocument();
    expect(screen.getByText("Definition Editor")).toBeInTheDocument();
    expect(screen.getByText("Routing Rules By Field")).toBeInTheDocument();
    expect(screen.getByText("Version Comparison")).toBeInTheDocument();
    expect(screen.getByText("Compare Against")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /3.1.0 \(published\)/ })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Template Catalog" })).toBeInTheDocument();
    expect(screen.queryByText("Open")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete Selected Draft" })).toBeInTheDocument();
    expect(screen.getByText("Routing Rules: 1")).toBeInTheDocument();
    expect(screen.getByText("Artifact Types: 1")).toBeInTheDocument();
    expect(screen.getByText("Added Promotion Rules")).toBeInTheDocument();
    expect(screen.getByText("Changed Fields")).toBeInTheDocument();
    expect(screen.getByText(/title: Subject -> Subject Area/)).toBeInTheDocument();
  });
});
