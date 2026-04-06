import { render, screen } from "@testing-library/react";
import React from "react";

import AdminDomainPackDetailPage from "./page";

vi.mock("next/link", () => ({
  default: ({ href, children, prefetch: _prefetch, ...props }: { href: string; children: React.ReactNode; prefetch?: boolean }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/lib/server-api", () => ({
  getDomainPack: vi.fn(async () => ({
    pack: {
      id: "dp_001",
      tenant_id: "tenant_demo",
      name: "Assessment Governance Pack",
      version: "1.0.0",
      description: "Extends assessment workflows and policies.",
      status: "draft",
      contributed_templates: ["tmpl_assessment"],
      contributed_artifact_types: ["knowledge_note"],
      contributed_workflows: ["wf_assessment_revision_v1"],
      contributed_policies: ["pol_assessment_review"],
      activated_at: null,
      created_at: "2026-04-02T10:00:00Z",
      updated_at: "2026-04-02T10:00:00Z",
    },
    installations: [
      {
        id: "dpi_001",
        tenant_id: "tenant_demo",
        pack_id: "dp_001",
        installed_version: "1.0.0",
        status: "installed",
        installed_by: "user_demo",
        installed_at: "2026-04-02T10:11:00Z",
      },
    ],
  })),
  validateDomainPack: vi.fn(async () => []),
  compareDomainPack: vi.fn(async () => ({
    current_pack_id: "dp_001",
    current_version: "1.0.0",
    baseline_pack_id: "dp_000",
    baseline_version: "0.9.0",
    summary: "Compared with 0.9.0: 2 additions and 1 removals across declared contributions.",
    deltas: [
      { category: "templates", added: ["tmpl_assessment"], removed: [] },
      { category: "artifact_types", added: ["knowledge_note"], removed: [] },
      { category: "workflows", added: [], removed: ["wf_legacy"] },
      { category: "policies", added: [], removed: [] },
    ],
  })),
  listDomainPackLineage: vi.fn(async () => [
    {
      pack_id: "dp_001",
      version: "1.0.0",
      status: "draft",
      created_at: "2026-04-02T10:00:00Z",
      activated_at: null,
      contribution_count: 4,
    },
    {
      pack_id: "dp_000",
      version: "0.9.0",
      status: "deprecated",
      created_at: "2026-03-29T10:00:00Z",
      activated_at: "2026-03-29T11:00:00Z",
      contribution_count: 3,
    },
  ]),
}));

describe("AdminDomainPackDetailPage", () => {
  it("renders validation, comparison, and lineage for the selected pack", async () => {
    render(await AdminDomainPackDetailPage({ params: Promise.resolve({ packId: "dp_001" }) }));

    expect(screen.getByRole("heading", { name: "Assessment Governance Pack" })).toBeInTheDocument();
    expect(screen.getByText("Validation")).toBeInTheDocument();
    expect(screen.getByText("Pack contributions satisfy the current governance checks.")).toBeInTheDocument();
    expect(screen.getByText("Version Comparison")).toBeInTheDocument();
    expect(screen.getByText("Compared with 0.9.0: 2 additions and 1 removals across declared contributions.")).toBeInTheDocument();
    expect(screen.getByText("Version Lineage")).toBeInTheDocument();
    expect(screen.getAllByText("0.9.0").length).toBeGreaterThan(0);
    expect(screen.getByText("4")).toBeInTheDocument();
  });
});
