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
  ])
}));

describe("AdminTemplatesPage", () => {
  it("renders the catalog-first template index with drill-down links", async () => {
    const ui = await AdminTemplatesPage();
    render(ui);

    expect(screen.getByText("Catalog Summary")).toBeInTheDocument();
    expect(screen.queryByText("Definition Editor")).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "Curriculum Generation" }).some(
        (link) => link.getAttribute("href") === "/admin/templates/tmpl_curriculum/3.2.0",
      ),
    ).toBe(true);
    expect(screen.getAllByRole("link", { name: "Open Version" }).length).toBeGreaterThan(0);
  });
});
