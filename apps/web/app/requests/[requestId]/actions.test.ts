import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const submitRequestMock = vi.fn();
const bindRequestToNodeMock = vi.fn();
const updateRequestNodeExecutionMock = vi.fn();
const cancelRequestMock = vi.fn();
const cloneRequestMock = vi.fn();
const transitionRequestMock = vi.fn();
const runRequestChecksMock = vi.fn();
const assignAgentSessionMock = vi.fn();
const revalidatePathMock = vi.fn();
const redirectMock = vi.fn((location: string) => {
  throw new Error(`REDIRECT:${location}`);
});
const isRedirectErrorMock = vi.fn((error: unknown) => error instanceof Error && error.message.startsWith("REDIRECT:"));

vi.mock("@/lib/server-api", () => ({
  submitRequest: submitRequestMock,
  bindRequestToNode: bindRequestToNodeMock,
  updateRequestNodeExecution: updateRequestNodeExecutionMock,
  cancelRequest: cancelRequestMock,
  cloneRequest: cloneRequestMock,
  transitionRequest: transitionRequestMock,
  runRequestChecks: runRequestChecksMock,
  assignAgentSession: assignAgentSessionMock
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

describe("request detail actions", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submits requests with a durable reason and revalidates request views", async () => {
    const { submitRequestAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");

    await submitRequestAction(formData);

    expect(submitRequestMock).toHaveBeenCalledWith("req_001", {
      reason: "Submitted from request detail"
    });
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests/req_001");
    expect(revalidatePathMock).toHaveBeenCalledWith("/requests");
  });

  it("binds a request to a node and preserves the optional environment id", async () => {
    const { bindRequestToNodeAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");
    formData.set("nodeId", "node_123");
    formData.set("environmentId", "env_local");

    await bindRequestToNodeAction(formData);

    expect(bindRequestToNodeMock).toHaveBeenCalledWith("req_001", {
      node_id: "node_123",
      environment_id: "env_local",
      reason: "Request bound from request detail"
    });
  });

  it("rejects missing node ids for local execution mutations", async () => {
    const { markRequestNodeExecutingAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");

    await expect(markRequestNodeExecutingAction(formData)).rejects.toThrow("Missing nodeId");
    expect(updateRequestNodeExecutionMock).not.toHaveBeenCalled();
  });

  it("marks a request as awaiting central approval with the expected local status", async () => {
    const { markRequestAwaitingCentralApprovalAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");
    formData.set("nodeId", "node_123");

    await markRequestAwaitingCentralApprovalAction(formData);

    expect(updateRequestNodeExecutionMock).toHaveBeenCalledWith("req_001", {
      node_id: "node_123",
      local_status: "awaiting_central_approval",
      reason: "Node reported central approval gate from request detail"
    });
  });

  it("redirects cloned requests to the new request detail page", async () => {
    cloneRequestMock.mockResolvedValueOnce({ id: "req_clone_001" });
    const { cloneRequestAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");

    await expect(cloneRequestAction(formData)).rejects.toThrow("REDIRECT:/requests/req_clone_001");

    expect(cloneRequestMock).toHaveBeenCalledWith("req_001", {
      reason: "Cloned from request detail"
    });
    expect(redirectMock).toHaveBeenCalledWith("/requests/req_clone_001");
  });

  it("transitions requests to the chosen status with an audit-friendly reason", async () => {
    const { transitionRequestAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");
    formData.set("targetStatus", "queued");

    await transitionRequestAction(formData);

    expect(transitionRequestMock).toHaveBeenCalledWith("req_001", {
      target_status: "queued",
      reason: "Transitioned from request detail to queued"
    });
  });

  it("redirects agent assignment failures back to the agents view with context", async () => {
    assignAgentSessionMock.mockRejectedValueOnce(new Error("Integration unavailable"));
    const { assignAgentSessionAction } = await import("./actions");
    const formData = new FormData();
    formData.set("requestId", "req_001");
    formData.set("integrationId", "int_agent_codex");
    formData.set("initialPrompt", "Review this request.");
    formData.set("collaborationMode", "agent_assisted");
    formData.set("agentOperatingProfile", "general");

    await expect(assignAgentSessionAction(formData)).rejects.toThrow(
      "REDIRECT:/requests/req_001/agents?error=Integration+unavailable&integration=int_agent_codex&collaboration_mode=agent_assisted&agent_operating_profile=general"
    );

    expect(redirectMock).toHaveBeenCalledWith(
      "/requests/req_001/agents?error=Integration+unavailable&integration=int_agent_codex&collaboration_mode=agent_assisted&agent_operating_profile=general"
    );
  });
});
