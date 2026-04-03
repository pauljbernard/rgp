import { render, screen } from "@testing-library/react";
import NewRequestPage from "./page";

vi.mock("@/lib/server-api", () => ({
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
    expect(screen.getByRole("link", { name: "Choose Different Template" })).toHaveAttribute(
      "href",
      "/requests/new?template=tmpl_assessment%401.4.0&choose_template=1",
    );
  });
});
