import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const createAssignmentGroupMock = vi.fn();
const createEscalationRuleMock = vi.fn();
const createSlaDefinitionMock = vi.fn();
const remediateSlaBreachMock = vi.fn();
const revalidatePathMock = vi.fn();
const redirectMock = vi.fn((location: string) => {
  throw new Error(`REDIRECT:${location}`);
});

vi.mock("@/lib/server-api", () => ({
  createAssignmentGroup: createAssignmentGroupMock,
  createEscalationRule: createEscalationRuleMock,
  createSlaDefinition: createSlaDefinitionMock,
  remediateSlaBreach: remediateSlaBreachMock
}));

vi.mock("next/cache", () => ({
  revalidatePath: revalidatePathMock
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

describe("queues actions", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("normalizes assignment group form values before redirecting back to queues", async () => {
    createAssignmentGroupMock.mockResolvedValueOnce({ id: "ag_001" });
    const { createAssignmentGroupAction } = await import("./actions");
    const formData = new FormData();
    formData.set("name", "  Editorial Reviewers  ");
    formData.set("skillTags", " editorial, review , legal ");
    formData.set("maxCapacity", "8");

    await expect(createAssignmentGroupAction(formData)).rejects.toThrow("REDIRECT:/queues");

    expect(createAssignmentGroupMock).toHaveBeenCalledWith({
      name: "Editorial Reviewers",
      skill_tags: ["editorial", "review", "legal"],
      max_capacity: 8
    });
    expect(revalidatePathMock).toHaveBeenCalledWith("/queues");
  });

  it("builds escalation rule conditions from the status form field", async () => {
    createEscalationRuleMock.mockResolvedValueOnce({ id: "er_001" });
    const { createEscalationRuleAction } = await import("./actions");
    const formData = new FormData();
    formData.set("name", "Stale Review Escalation");
    formData.set("escalationTarget", "queue_lead");
    formData.set("statusValue", "awaiting_review");
    formData.set("delayMinutes", "90");

    await expect(createEscalationRuleAction(formData)).rejects.toThrow("REDIRECT:/queues");

    expect(createEscalationRuleMock).toHaveBeenCalledWith({
      name: "Stale Review Escalation",
      escalation_target: "queue_lead",
      escalation_type: "reassign",
      delay_minutes: 90,
      condition: { field: "status", equals: "awaiting_review" }
    });
  });

  it("maps optional SLA definition fields before redirecting to queues", async () => {
    createSlaDefinitionMock.mockResolvedValueOnce({ id: "sla_001" });
    const { createSlaDefinitionAction } = await import("./actions");
    const formData = new FormData();
    formData.set("name", "Assessment Review SLA");
    formData.set("scopeType", "request_type");
    formData.set("scopeId", "assessment");
    formData.set("responseTargetHours", "4");
    formData.set("resolutionTargetHours", "24");
    formData.set("reviewDeadlineHours", "8");

    await expect(createSlaDefinitionAction(formData)).rejects.toThrow("REDIRECT:/queues");

    expect(createSlaDefinitionMock).toHaveBeenCalledWith({
      name: "Assessment Review SLA",
      scope_type: "request_type",
      scope_id: "assessment",
      response_target_hours: 4,
      resolution_target_hours: 24,
      review_deadline_hours: 8
    });
  });

  it("rejects missing SLA breach remediation fields before calling the API", async () => {
    const { remediateSlaBreachAction } = await import("./actions");
    const formData = new FormData();
    formData.set("breachId", "sb_001");

    await expect(remediateSlaBreachAction(formData)).rejects.toThrow("Missing SLA breach remediation fields");
    expect(remediateSlaBreachMock).not.toHaveBeenCalled();
  });

  it("revalidates dependent pages when remediating an SLA breach", async () => {
    remediateSlaBreachMock.mockResolvedValueOnce({ id: "sb_001" });
    const { remediateSlaBreachAction } = await import("./actions");
    const formData = new FormData();
    formData.set("breachId", "sb_001");
    formData.set("remediationAction", "queue_lead_notified");

    await expect(remediateSlaBreachAction(formData)).rejects.toThrow("REDIRECT:/queues");

    expect(remediateSlaBreachMock).toHaveBeenCalledWith("sb_001", {
      remediation_action: "queue_lead_notified"
    });
    expect(revalidatePathMock).toHaveBeenCalledWith("/queues");
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests/sla-risk");
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests");
  });
});
