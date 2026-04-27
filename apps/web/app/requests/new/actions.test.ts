import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const createRequestDraftMock = vi.fn();
const revalidatePathMock = vi.fn();
const redirectMock = vi.fn((location: string) => {
  throw new Error(`REDIRECT:${location}`);
});
const isRedirectErrorMock = vi.fn((error: unknown) => error instanceof Error && error.message.startsWith("REDIRECT:"));

vi.mock("@/lib/server-api", () => ({
  createRequestDraft: createRequestDraftMock
}));

vi.mock("next/cache", () => ({
  revalidatePath: revalidatePathMock
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

vi.mock("next/dist/client/components/redirect-error", () => ({
  isRedirectError: isRedirectErrorMock
}));

describe("createRequestAction", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("creates a draft, revalidates the request list, and redirects to the new request", async () => {
    createRequestDraftMock.mockResolvedValueOnce({ id: "req_123" });
    const { createRequestAction } = await import("./actions");
    const formData = new FormData();
    formData.set("templateId", "tmpl_assessment");
    formData.set("templateVersion", "1.4.0");
    formData.set("title", "Assessment Refresh");
    formData.set("summary", "Request summary");
    formData.set("priority", "high");
    formData.set("executionMode", "federated_local");
    formData.set("assignedNodeId", "node_001");
    formData.set("input_assessment_id", "asm_001");
    formData.set("input_revision_reason", "Standards alignment");
    formData.set("input_empty", "");

    await expect(createRequestAction(formData)).rejects.toThrow("REDIRECT:/requests/req_123");

    expect(createRequestDraftMock).toHaveBeenCalledWith({
      template_id: "tmpl_assessment",
      template_version: "1.4.0",
      title: "Assessment Refresh",
      summary: "Request summary",
      priority: "high",
      execution_mode: "federated_local",
      assigned_node_id: "node_001",
      input_payload: {
        assessment_id: "asm_001",
        revision_reason: "Standards alignment"
      }
    });
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests");
    expect(redirectMock).toHaveBeenCalledWith("/requests/req_123");
  });

  it("redirects back to the request form with the encoded error message on failure", async () => {
    createRequestDraftMock.mockRejectedValueOnce(new Error("Duplicate request draft"));
    const { createRequestAction } = await import("./actions");
    const formData = new FormData();
    formData.set("templateId", "tmpl_assessment");
    formData.set("templateVersion", "1.4.0");
    formData.set("title", "Assessment Refresh");
    formData.set("summary", "Request summary");
    formData.set("priority", "medium");
    formData.set("executionMode", "central");

    await expect(createRequestAction(formData)).rejects.toThrow(
      "REDIRECT:/requests/new?template=tmpl_assessment%401.4.0&error=Duplicate%20request%20draft"
    );

    expect(revalidatePathMock).not.toHaveBeenCalled();
    expect(redirectMock).toHaveBeenCalledWith(
      "/requests/new?template=tmpl_assessment%401.4.0&error=Duplicate%20request%20draft"
    );
  });

  it("rejects invalid payloads before calling the API", async () => {
    const { createRequestAction } = await import("./actions");
    const formData = new FormData();
    formData.set("templateId", "tmpl_assessment");

    await expect(createRequestAction(formData)).rejects.toThrow("Invalid request payload");
    expect(createRequestDraftMock).not.toHaveBeenCalled();
  });
});
