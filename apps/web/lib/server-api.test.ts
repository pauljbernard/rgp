import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn((location: string) => {
  throw new Error(`REDIRECT:${location}`);
});
const cookiesMock = vi.fn();

vi.mock("next/headers", () => ({
  cookies: cookiesMock
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

describe("server-api", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    cookiesMock.mockResolvedValue({
      get: vi.fn(() => ({ value: "token_demo" }))
    });
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("serializes request list filters and attaches the bearer token", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [], page: 2, page_size: 10, total_count: 0, total_pages: 0 })
    } as Response);
    const serverApi = await import("./server-api");

    await serverApi.listRequests({
      page: 2,
      page_size: 10,
      status: "awaiting_review",
      request_id: "req_123"
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/requests?page=2&page_size=10&status=awaiting_review&request_id=req_123"),
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          Authorization: "Bearer token_demo",
          "Content-Type": "application/json"
        })
      })
    );
  });

  it("raises the API detail message when a mutation fails", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "Duplicate request draft" })
    } as Response);
    const serverApi = await import("./server-api");

    await expect(
      serverApi.createRequestDraft({
        template_id: "tmpl_assessment",
        template_version: "1.4.0",
        title: "Assessment Refresh",
        summary: "Duplicate request scenario.",
        priority: "medium"
      })
    ).rejects.toThrow("Duplicate request draft");
  });

  it("redirects forbidden responses to the dedicated forbidden route", async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Forbidden" })
    } as Response);
    const serverApi = await import("./server-api");

    await expect(serverApi.listAssignmentGroups()).rejects.toThrow(
      "REDIRECT:/forbidden?from=%2Fapi%2Fv1%2Fqueue-routing%2Fgroups"
    );
    expect(redirectMock).toHaveBeenCalledWith("/forbidden?from=%2Fapi%2Fv1%2Fqueue-routing%2Fgroups");
  });
});
