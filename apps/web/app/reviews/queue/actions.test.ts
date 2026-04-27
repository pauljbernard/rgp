import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const recordReviewDecisionMock = vi.fn();
const overrideReviewAssignmentMock = vi.fn();
const revalidatePathMock = vi.fn();

vi.mock("@/lib/server-api", () => ({
  recordReviewDecision: recordReviewDecisionMock,
  overrideReviewAssignment: overrideReviewAssignmentMock
}));

vi.mock("next/cache", () => ({
  revalidatePath: revalidatePathMock
}));

describe("review queue actions", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("records a queue review decision with a durable reason and revalidates views", async () => {
    recordReviewDecisionMock.mockResolvedValueOnce({ id: "revq_001" });
    const { reviewDecisionAction } = await import("./actions");
    const formData = new FormData();
    formData.set("reviewId", "revq_001");
    formData.set("decision", "approve");

    await reviewDecisionAction(formData);

    expect(recordReviewDecisionMock).toHaveBeenCalledWith("revq_001", {
      decision: "approve",
      reason: "Review decision submitted from queue: approve"
    });
    expect(revalidatePathMock).toHaveBeenCalledWith("/reviews/queue");
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests");
  });

  it("rejects incomplete review assignment override payloads", async () => {
    const { overrideReviewAssignmentAction } = await import("./actions");
    const formData = new FormData();
    formData.set("reviewId", "revq_001");

    await expect(overrideReviewAssignmentAction(formData)).rejects.toThrow("Missing review override fields");
    expect(overrideReviewAssignmentMock).not.toHaveBeenCalled();
  });

  it("sends the replacement reviewer and rationale for overrides", async () => {
    overrideReviewAssignmentMock.mockResolvedValueOnce({ id: "revq_001" });
    const { overrideReviewAssignmentAction } = await import("./actions");
    const formData = new FormData();
    formData.set("reviewId", "revq_001");
    formData.set("assignedReviewer", "reviewer_nina");

    await overrideReviewAssignmentAction(formData);

    expect(overrideReviewAssignmentMock).toHaveBeenCalledWith("revq_001", {
      assigned_reviewer: "reviewer_nina",
      reason: "Review assignment overridden from queue: reviewer_nina"
    });
    expect(revalidatePathMock).toHaveBeenCalledWith("/reviews/queue");
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests");
  });
});
