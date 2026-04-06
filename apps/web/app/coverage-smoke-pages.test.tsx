import { render, screen } from "@testing-library/react";
import React from "react";
import AnalyticsPage from "./analytics/page";
import AgentAnalyticsPage from "./analytics/agents/page";
import BottleneckAnalyticsPage from "./analytics/bottlenecks/page";
import AnalyticsCostPage from "./analytics/cost/page";
import DeliveryAnalyticsPage from "./analytics/delivery/page";
import PerformanceAnalyticsPage from "./analytics/performance/page";
import WorkflowAnalyticsPage from "./analytics/workflows/page";
import WorkflowFederationPage from "./analytics/workflows/[workflow]/federation/page";
import WorkflowHistoryPage from "./analytics/workflows/[workflow]/history/page";
import AdminIntegrationsPage from "./admin/integrations/page";
import AdminIntegrationDetailPage from "./admin/integrations/[integrationId]/page";
import AdminDomainPackDetailPage from "./admin/domain-packs/[packId]/page";
import AdminDomainPacksPage from "./admin/domain-packs/page";
import AdminOrgPage from "./admin/org/page";
import AdminTeamDetailPage from "./admin/org/teams/[teamId]/page";
import AdminUserDetailPage from "./admin/org/users/[userId]/page";
import AdminPoliciesPage from "./admin/policies/page";
import ArtifactsPage from "./artifacts/page";
import ArtifactDetailPage from "./artifacts/[artifactId]/page";
import CapabilitiesPage from "./capabilities/page";
import CapabilityDetailPage from "./capabilities/[capabilityId]/page";
import ForbiddenPage from "./forbidden/page";
import HelpAnalyticsPage from "./help/analytics/page";
import HelpAdminPage from "./help/admin/page";
import HelpJourneysPage from "./help/journeys/page";
import HelpOperationsPage from "./help/operations/page";
import HelpOverviewPage from "./help/page";
import HelpRequestsPage from "./help/requests/page";
import KnowledgeArtifactDetailPage from "./knowledge/[artifactId]/page";
import NewKnowledgeArtifactPage from "./knowledge/new/page";
import KnowledgePage from "./knowledge/page";
import PlanningConstructDetailPage from "./planning/[constructId]/page";
import NewPlanningConstructPage from "./planning/new/page";
import PlanningPage from "./planning/page";
import PromotionPage from "./promotions/[promotionId]/page";
import PromotionPendingPage from "./promotions/pending/page";
import QueuesPage from "./queues/page";
import ReviewQueuePage from "./reviews/queue/page";
import SlaRiskRequestsPage from "./requests/sla-risk/page";
import RequestAgentsPage from "./requests/[requestId]/agents/page";
import RequestHistoryPage from "./requests/[requestId]/history/page";
import RequestProjectionPage from "./requests/[requestId]/projections/[projectionId]/page";
import RequestDetailPage from "./requests/[requestId]/page";
import RequestAgentSessionPage from "./requests/[requestId]/agents/[sessionId]/page";
import RequestFederatedConflictsPage from "./requests/federated-conflicts/page";
import RunsPage from "./runs/page";
import FailedRunsPage from "./runs/failed/page";
import RunDetailPage from "./runs/[runId]/page";
import RunHistoryPage from "./runs/[runId]/history/page";
import RegisterPage from "./register/page";

vi.mock("@/lib/server-api", () => {
  const requestRecord = {
    id: "req_001",
    tenant_id: "tenant_demo",
    request_type: "assessment",
    template_id: "tmpl_assessment",
    template_version: "1.4.0",
    title: "Assessment Refresh",
    summary: "Refresh benchmark assessment.",
    status: "awaiting_review",
    priority: "high",
    sla_policy_id: null,
    submitter_id: "user_demo",
    owner_team_id: "team_assessment_quality",
    owner_user_id: "user_demo",
    workflow_binding_id: "wf_assessment_revision_v1",
    current_run_id: "run_001",
    policy_context: {},
    input_payload: { assessment_id: "asm_001" },
    tags: [],
    created_at: "2026-04-02T10:00:00Z",
    created_by: "user_demo",
    updated_at: "2026-04-02T10:30:00Z",
    updated_by: "user_demo",
    version: 1,
    is_archived: false,
    sla_risk_level: "high",
    sla_risk_reason: "Review delay",
    federated_projection_count: 1,
    federated_conflict_count: 1
  };

  const requestDetail = {
    request: requestRecord,
    next_required_action: "Review required",
    active_blockers: ["Awaiting reviewer decision"],
    latest_run_id: "run_001",
    latest_artifact_ids: ["art_001"],
    predecessors: [],
    successors: [],
    check_results: [
      { id: "chk_001", name: "Policy Pack", state: "passed", detail: "All checks passed", evidence: "evidence", severity: "low", evaluated_by: "system" }
    ],
    check_runs: [
      { id: "cr_001", scope: "request", status: "completed", trigger_reason: "submit", enqueued_by: "system", queued_at: "2026-04-02T10:00:00Z" }
    ],
    agent_sessions: [
      { id: "ags_001", agent_label: "Codex", status: "waiting_on_human", summary: "Ready for review", integration_name: "OpenAI Codex", message_count: 2, awaiting_human: true }
    ]
  };

  const agentSession = {
    id: "ags_001",
    request_id: "req_001",
    integration_id: "int_agent_codex",
    integration_name: "OpenAI Codex",
    provider: "openai",
    agent_label: "Codex",
    collaboration_mode: "agent_assisted",
    agent_operating_profile: "review",
    status: "waiting_on_human",
    summary: "Proposed an updated assessment outline.",
    awaiting_human: true,
    assigned_by: "user_demo",
    assigned_at: "2026-04-02T10:00:00Z",
    external_session_ref: "sess_123",
    message_count: 2,
    latest_message: { id: "msg_002", sender_type: "agent", sender_id: "codex", body: "Updated outline with three recommendations.", created_at: "2026-04-02T10:05:00Z" },
    messages: [
      { id: "msg_001", sender_type: "human", sender_id: "user_demo", body: "Please improve the assessment.", created_at: "2026-04-02T10:00:00Z" },
      { id: "msg_002", sender_type: "agent", sender_id: "codex", body: "Updated outline with three recommendations.", created_at: "2026-04-02T10:05:00Z" }
    ]
  };

  const agentSessionContext = {
    bundle: {
      id: "cb_001",
      tenant_id: "tenant_demo",
      request_id: "req_001",
      session_id: "ags_001",
      version: 2,
      bundle_type: "agent_session",
      contents: {
        request_data: { title: "Assessment Refresh" },
        template_semantics: { template_id: "tmpl_assessment" },
        workflow_state: { current_step: "review" },
        available_tools: [{ name: "request.summary" }],
        knowledge_context: [
          {
            artifact_id: "ka_001",
            name: "Assessment Review Playbook",
            description: "Published guidance",
            content_type: "markdown",
            version: 2,
            tags: ["review", "policy"]
          }
        ]
      },
      policy_scope: { collaboration_mode: "agent_assisted" },
      assembled_by: "user_demo",
      assembled_at: "2026-04-02T10:00:00Z",
      provenance: [{ source: "request", id: "req_001" }]
    },
    available_tools: [
      {
        name: "request.summary",
        description: "Read the governed request summary.",
        input_schema: {},
        required_collaboration_mode: "agent_assisted",
        allowed_roles: [],
        availability: "available"
      }
    ],
    restricted_tools: [
      {
        name: "request.timeline",
        description: "Inspect the governed request and workflow timeline.",
        input_schema: {},
        required_collaboration_mode: "agent_assisted",
        allowed_roles: [],
        availability: "denied",
        availability_reason: "Restricted by session policy."
      }
    ],
    degraded_tools: [
      {
        name: "request.relationships",
        description: "Inspect dependency and related-request context from the governed graph.",
        input_schema: {},
        required_collaboration_mode: null,
        allowed_roles: [],
        availability: "degraded",
        availability_reason: "No governed request relationships are currently attached."
      }
    ],
    capability_warnings: [],
    access_log: [
      {
        id: "cal_001",
        bundle_id: "cb_001",
        accessor_type: "agent",
        accessor_id: "int_agent_codex",
        accessed_resource: "mcp_tool:request.summary",
        access_result: "granted",
        policy_basis: { collaboration_mode: "agent_assisted" },
        accessed_at: "2026-04-02T10:01:00Z"
      }
    ]
  };

  const runRecord = {
    id: "run_001",
    request_id: "req_001",
    workflow: "wf_assessment_revision_v1",
    workflow_identity: "tmpl_assessment",
    status: "awaiting_review",
    current_step: "review",
    elapsed_time: "12m",
    waiting_reason: "Awaiting review",
    owner: "team_assessment_quality",
    updated_at: "2026-04-02T10:30:00Z",
    federated_projection_count: 1,
    federated_conflict_count: 1
  };

  const runDetail = {
    ...runRecord,
    owner_team: "team_assessment_quality",
    progress_percent: 65,
    current_step_input_summary: "Assessment payload loaded.",
    current_step_output_summary: "Review package assembled.",
    command_surface: ["Resume", "Cancel Run"],
    run_context: [["Owner Team", "team_assessment_quality"], ["Template", "tmpl_assessment@1.4.0"]],
    runtime_dispatches: [{ dispatched_at: "2026-04-02T10:01:00Z", dispatch_type: "worker", status: "completed", integration_id: "int_agent_codex", external_reference: "ext_001", detail: "queued" }],
    runtime_signals: [{ received_at: "2026-04-02T10:02:00Z", event_id: "sig_001", source: "worker", status: "completed", current_step: "review", detail: "signal received" }],
    federated_projections: [
      {
        id: "pm_001",
        tenant_id: "tenant_demo",
        integration_id: "int_agent_codex",
        entity_type: "request",
        entity_id: "req_001",
        external_system: "OpenAI Codex",
        external_ref: "int_agent_codex:request:req_001",
        external_state: { status: "external_review", projection_form: "agent_session", agent_state: { session_status: "active" } },
        projection_status: "synced",
        last_projected_at: "2026-04-02T10:00:00Z",
        last_synced_at: "2026-04-02T10:10:00Z",
        adapter_type: "openai_projection",
        adapter_capabilities: ["project", "query_external_state", "reconcile", "capability_discovery"],
        sync_source: "adapter:openai_projection",
        conflicts: [{ field: "status", internal: "awaiting_review", external: "external_review" }],
        supported_resolution_actions: ["accept_internal", "accept_external", "resume_session"],
        resolution_guidance: "Use resume_session when the external agent session should be resumed under governed state."
      }
    ],
    started_at: "2026-04-02T10:00:00Z",
    completed_at: null,
    steps: [
      { id: "step_001", name: "Draft", status: "completed", actor: "system", started_at: "2026-04-02T10:00:00Z", completed_at: "2026-04-02T10:05:00Z", detail: "Drafted." },
      { id: "step_002", name: "Review", status: "running", actor: "reviewer_nina", started_at: "2026-04-02T10:06:00Z", completed_at: null, detail: "In review." }
    ],
    commands: [
      { name: "rerun", label: "Rerun", command: "rerun" }
    ],
    artifacts: [{ id: "art_001", name: "Assessment Draft" }],
    history: [{ timestamp: "2026-04-02T10:06:00Z", actor: "system", action: "entered review" }]
  };

  const team = {
    id: "team_assessment_quality",
    tenant_id: "tenant_demo",
    organization_id: "org_assessment",
    organization_name: "Assessment and Quality",
    name: "Assessment Quality",
    kind: "delivery",
    status: "active",
    member_count: 2,
    members: [
      { user_id: "user_demo", display_name: "Demo User", email: "demo@example.com", role: "lead" },
      { user_id: "reviewer_nina", display_name: "Reviewer Nina", email: "nina@example.com", role: "reviewer" }
    ]
  };
  const organization = { id: "org_assessment", tenant_id: "tenant_demo", name: "Assessment and Quality", status: "active" };
  const tenant = { id: "tenant_demo", name: "Demo Tenant", status: "active", organization_count: 1 };

  const user = {
    id: "user_demo",
    tenant_id: "tenant_demo",
    display_name: "Demo User",
    email: "demo@example.com",
    status: "active",
    roles: ["admin"],
    role_summary: ["admin"],
    team_ids: ["team_assessment_quality"],
    has_password: true,
    password_reset_required: false,
    registration_request_id: null
  };
  const pendingUser = {
    id: "user_pending",
    tenant_id: "tenant_demo",
    display_name: "Pending User",
    email: "pending@example.com",
    status: "pending_activation",
    roles: ["submitter"],
    role_summary: ["submitter"],
    team_ids: [],
    has_password: false,
    password_reset_required: true,
    registration_request_id: "req_registration_001"
  };
  const portfolio = { id: "port_assessment", tenant_id: "tenant_demo", name: "Assessment Portfolio", owner_team_id: "team_assessment_quality", scope_keys: ["team_assessment_quality"], status: "active" };
  const integration = {
    id: "int_agent_codex",
    name: "OpenAI Codex",
    type: "agent",
    status: "active",
    endpoint: "https://api.openai.com/v1",
    resolved_endpoint: "https://api.openai.com/v1/responses",
    supports_direct_assignment: true,
    supports_interactive_sessions: true,
    has_api_key: true,
    has_access_token: true,
    settings: { provider: "openai", base_url: "https://api.openai.com/v1", model: "gpt-5.4", workspace_id: "default" }
  };
  const projection = {
    id: "pm_001",
    tenant_id: "tenant_demo",
    integration_id: "int_agent_codex",
    entity_type: "request",
    entity_id: "req_001",
    external_system: "OpenAI Codex",
    external_ref: "int_agent_codex:request:req_001",
    external_state: { status: "external_review", projection_form: "agent_session", agent_state: { session_status: "active" } },
    projection_status: "synced",
    last_projected_at: "2026-04-02T10:00:00Z",
    last_synced_at: "2026-04-02T10:10:00Z",
    adapter_type: "openai_projection",
    adapter_capabilities: ["project", "query_external_state", "reconcile", "capability_discovery"],
    sync_source: "adapter:openai_projection",
    conflicts: [{ field: "status", internal: "awaiting_review", external: "external_review" }],
    supported_resolution_actions: ["accept_internal", "accept_external", "resume_session"],
    resolution_guidance: "Use resume_session when the external agent session should be resumed under governed state."
  };
  const reconciliationLog = {
    id: "rl_001",
    projection_id: "pm_001",
    action: "updated",
    detail: "Projection pm_001 is in sync",
    resolved_by: null,
    created_at: "2026-04-02T10:11:00Z"
  };
  const domainPack = {
    id: "dp_001",
    tenant_id: "tenant_demo",
    name: "Content and Editorial Pack",
    version: "1.0.0",
    description: "Adds editorial templates and review policies.",
    status: "active",
    contributed_templates: ["tmpl_editorial"],
    contributed_artifact_types: ["document", "media"],
    contributed_workflows: ["wf_editorial_publish"],
    contributed_policies: ["pol_editorial_review"],
    activated_at: "2026-04-02T10:10:00Z",
    created_at: "2026-04-02T10:00:00Z",
    updated_at: "2026-04-02T10:10:00Z"
  };

  return {
    listRequests: vi.fn(async () => ({ items: [requestRecord], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    listRuns: vi.fn(async () => ({ items: [runRecord], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    getRun: vi.fn(async () => runDetail),
    getRunHistory: vi.fn(async () => [
      {
        timestamp: "2026-04-02T10:01:00Z",
        actor: "system",
        action: "Run Started",
        object_type: "run",
        object_id: "run_001",
        reason_or_evidence: "Workflow binding wf_assessment_revision_v1",
        event_class: "canonical",
        source_system: "RGP",
        integration_id: null,
        projection_id: null,
        related_entity_type: "request",
        related_entity_id: "req_001",
        lineage: ["request:req_001", "run:run_001"]
      },
      {
        timestamp: "2026-04-02T10:11:00Z",
        actor: "system",
        action: "Observed External State",
        object_type: "projection",
        object_id: "pm_001",
        reason_or_evidence: "Observed external state for request req_001",
        event_class: "federated_sync",
        source_system: "OpenAI Codex",
        integration_id: "int_agent_codex",
        projection_id: "pm_001",
        related_entity_type: "request",
        related_entity_id: "req_001",
        lineage: ["request:req_001", "projection:pm_001", "external:OpenAI Codex", "external_ref:int_agent_codex:request:req_001"]
      }
    ]),
    getWorkflowHistory: vi.fn(async () => [
      {
        timestamp: "2026-04-02T10:12:00Z",
        actor: "system",
        action: "Merge",
        object_type: "projection",
        object_id: "pm_001",
        reason_or_evidence: "Repository projection reconciled.",
        event_class: "federated_resolution",
        source_system: "GitHub",
        integration_id: "int_002",
        projection_id: "pm_001",
        related_entity_type: "workflow",
        related_entity_id: "tmpl_assessment",
        lineage: ["workflow:tmpl_assessment", "request:req_001", "projection:pm_001"]
      }
    ]),
    listArtifacts: vi.fn(async () => ({
      items: [
        {
          id: "art_001",
          type: "document",
          name: "Assessment Draft",
          current_version: "v1",
          status: "approved",
          request_id: "req_001",
          updated_at: "2026-04-02T10:10:00Z",
          owner: "team_assessment_quality"
        }
      ]
    })),
    getArtifact: vi.fn(async () => ({
      artifact: {
        id: "art_001",
        name: "Assessment Draft",
        status: "approved",
        owner: "team_assessment_quality"
      },
      selected_version_id: "artv_001",
      versions: [
        {
          id: "artv_001",
          label: "v1",
          summary: "Initial approved artifact",
          status: "approved",
          content: "artifact body"
        }
      ],
      review_state: "approved",
      stale_review: false,
      lineage: [
        {
          from_version_id: null,
          to_version_id: "artv_001",
          relation: "created_from_request",
          created_at: "2026-04-02T10:00:00Z"
        }
      ],
      history: [
        {
          timestamp: "2026-04-02T10:10:00Z",
          actor: "reviewer_nina",
          action: "approved",
          detail: "Artifact approved"
        }
      ]
    })),
    listPlanningConstructs: vi.fn(async () => [
      {
        id: "pc_001",
        tenant_id: "tenant_demo",
        type: "initiative",
        name: "Assessment Quality Initiative",
        description: "Cross-request planning container",
        owner_team_id: "team_assessment_quality",
        status: "active",
        priority: 5,
        target_date: "2026-06-30T00:00:00Z",
        capacity_budget: 40,
        created_at: "2026-04-01T00:00:00Z",
        updated_at: "2026-04-02T00:00:00Z"
      }
    ]),
    getPlanningRoadmap: vi.fn(async () => [
      {
        id: "pc_001",
        type: "initiative",
        name: "Assessment Quality Initiative",
        status: "active",
        priority: 5,
        target_date: "2026-06-30T00:00:00Z",
        capacity_budget: 40,
        member_count: 2,
        completion_pct: 50,
        completed_count: 1,
        in_progress_count: 1,
        blocked_count: 0,
        schedule_state: "on_track",
        owner_team_id: "team_assessment_quality"
      }
    ]),
    getPlanningConstruct: vi.fn(async () => ({
      construct: {
        id: "pc_001",
        tenant_id: "tenant_demo",
        type: "initiative",
        name: "Assessment Quality Initiative",
        description: "Cross-request planning container",
        owner_team_id: "team_assessment_quality",
        status: "active",
        priority: 5,
        target_date: "2026-06-30T00:00:00Z",
        capacity_budget: 40,
        created_at: "2026-04-01T00:00:00Z",
        updated_at: "2026-04-02T00:00:00Z"
      },
      memberships: [
        {
          id: "pm_001",
          planning_construct_id: "pc_001",
          request_id: "req_001",
          sequence: 1,
          priority: 5,
          added_at: "2026-04-02T00:00:00Z"
        }
      ],
      progress: {
        construct_id: "pc_001",
        total: 1,
        status_counts: { submitted: 1 },
        completion_pct: 0
      }
    })),
    listDomainPacks: vi.fn(async () => [domainPack]),
    getDomainPack: vi.fn(async () => ({
      pack: domainPack,
      installations: [
        {
          id: "dpi_001",
          tenant_id: "tenant_demo",
          pack_id: "dp_001",
          installed_version: "1.0.0",
          status: "installed",
          installed_by: "user_demo",
          installed_at: "2026-04-02T10:11:00Z"
        }
      ]
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
        { category: "policies", added: [], removed: [] }
      ]
    })),
    listDomainPackLineage: vi.fn(async () => [
      {
        pack_id: "dp_001",
        version: "1.0.0",
        status: "draft",
        created_at: "2026-04-02T10:00:00Z",
        activated_at: null,
        contribution_count: 4
      },
      {
        pack_id: "dp_000",
        version: "0.9.0",
        status: "deprecated",
        created_at: "2026-03-29T10:00:00Z",
        activated_at: "2026-03-29T11:00:00Z",
        contribution_count: 3
      }
    ]),
    listKnowledge: vi.fn(async () => ({
      items: [
        {
          id: "ka_001",
          tenant_id: "tenant_demo",
          name: "Assessment Review Playbook",
          description: "Reusable review guidance.",
          content: "Use governed review criteria.",
          content_type: "markdown",
          version: 2,
          status: "published",
          policy_scope: null,
          provenance: [],
          tags: ["policy", "review"],
          created_by: "user_demo",
          created_at: "2026-04-02T10:00:00Z",
          updated_at: "2026-04-02T10:10:00Z"
        }
      ],
      page: 1,
      page_size: 25,
      total_count: 1,
      total_pages: 1
    })),
    getKnowledgeArtifact: vi.fn(async () => ({
      id: "ka_001",
      tenant_id: "tenant_demo",
      name: "Assessment Review Playbook",
      description: "Reusable review guidance.",
      content: "Use governed review criteria.",
      content_type: "markdown",
      version: 2,
      status: "published",
      policy_scope: null,
      provenance: [],
      tags: ["policy", "review"],
      created_by: "user_demo",
      created_at: "2026-04-02T10:00:00Z",
      updated_at: "2026-04-02T10:10:00Z"
    })),
    listKnowledgeVersions: vi.fn(async () => [
      {
        id: "kav_002",
        artifact_id: "ka_001",
        version: 2,
        content: "Use governed review criteria.",
        summary: "Published guidance",
        author: "user_demo",
        created_at: "2026-04-02T10:10:00Z"
      }
    ]),
    listCapabilities: vi.fn(async () => ({
      items: [
        {
          id: "cap_001",
          name: "Assessment Review",
          type: "workflow",
          version: "1.0.0",
          status: "active",
          owner: "team_assessment_quality",
          updated_at: "2026-04-02T10:00:00Z",
          usage_count: 12
        }
      ]
    })),
    getCapability: vi.fn(async () => ({
      capability: {
        id: "cap_001",
        name: "Assessment Review",
        status: "active",
        owner: "team_assessment_quality"
      },
      usage: [
        ["Requests", "12"],
        ["Integrations", "1"]
      ],
      definition: "Reviews and refines governed assessment requests.",
      lineage: ["cap_000 -> cap_001"],
      history: [
        {
          timestamp: "2026-04-02T10:00:00Z",
          actor: "user_demo",
          action: "registered"
        }
      ]
    })),
    getRequest: vi.fn(async () => requestDetail),
    getRequestKnowledgeContext: vi.fn(async () => [
      {
        id: "ka_001",
        tenant_id: "tenant_demo",
        name: "Assessment Review Playbook",
        description: "Reusable review guidance.",
        content: "Use governed review criteria.",
        content_type: "markdown",
        version: 2,
        status: "published",
        policy_scope: null,
        provenance: [],
        tags: ["policy", "review"],
        created_by: "user_demo",
        created_at: "2026-04-02T10:00:00Z",
        updated_at: "2026-04-02T10:10:00Z"
      }
    ]),
    getRoutingRecommendation: vi.fn(async () => ({
      request_id: "req_001",
      recommended_group_id: "ag_001",
      recommended_group_name: "Assessment Reviewers",
      matched_skills: ["review", "assessment"],
      route_basis: ["skill overlap: review, assessment", "capacity: 2/6"],
      current_load: 2,
      max_capacity: 6,
      sla_status: "yellow",
      escalation_targets: ["queue_lead"]
    })),
    listAssignmentGroups: vi.fn(async () => [
      {
        id: "ag_001",
        tenant_id: "tenant_demo",
        name: "Assessment Reviewers",
        skill_tags: ["review", "policy"],
        max_capacity: 6,
        current_load: 2,
        status: "active",
        created_at: "2026-04-03T10:00:00Z"
      }
    ]),
    listEscalationRules: vi.fn(async () => [
      {
        id: "er_001",
        tenant_id: "tenant_demo",
        name: "Stale Review Escalation",
        condition: { field: "status", equals: "awaiting_review" },
        escalation_target: "queue_lead",
        escalation_type: "reassign",
        delay_minutes: 60,
        status: "active",
        created_at: "2026-04-03T10:00:00Z"
      }
    ]),
    listSlaDefinitions: vi.fn(async () => [
      {
        id: "sla_001",
        tenant_id: "tenant_demo",
        name: "Assessment Review SLA",
        scope_type: "request_type",
        scope_id: "assessment",
        response_target_hours: 4,
        resolution_target_hours: 24,
        review_deadline_hours: 8,
        warning_threshold_pct: 70,
        status: "active",
        created_at: "2026-04-03T10:00:00Z"
      }
    ]),
    listSlaBreaches: vi.fn(async () => [
      {
        id: "sb_001",
        tenant_id: "tenant_demo",
        sla_definition_id: "sla_001",
        request_id: "req_001",
        breach_type: "review",
        target_hours: 8,
        actual_hours: 11,
        severity: "high",
        remediation_action: null,
        breached_at: "2026-04-03T12:00:00Z"
      }
    ]),
    listRequestEscalations: vi.fn(async () => [
      {
        id: "er_001",
        tenant_id: "tenant_demo",
        name: "Stale Review Escalation",
        condition: { field: "status", equals: "awaiting_review" },
        escalation_target: "team_queue_lead",
        escalation_type: "reassign",
        delay_minutes: 60,
        status: "active",
        created_at: "2026-04-03T12:00:00Z"
      }
    ]),
    listRequestProjections: vi.fn(async () => [projection]),
    listRequestAgentIntegrations: vi.fn(async () => [integration]),
    getRequestAgentAssignmentPreview: vi.fn(async () => agentSessionContext),
    getAgentSession: vi.fn(async () => agentSession),
    getAgentSessionContext: vi.fn(async () => agentSessionContext),
    listReviewQueue: vi.fn(async () => ({
      items: [
        {
          id: "revq_001",
          request_id: "req_001",
          review_scope: "request",
          artifact_or_changeset: "art_001",
          type: "compliance",
          priority: "high",
          sla: "4h",
          blocking_status: "blocking",
          assigned_reviewer: "reviewer_nina",
          stale: false
        }
      ],
      page: 1,
      page_size: 25,
      total_count: 1,
      total_pages: 1
    })),
    getRequestHistory: vi.fn(async () => [
      {
        timestamp: "2026-04-02T10:00:00Z",
        actor: "user_demo",
        action: "submitted",
        object_type: "request",
        object_id: "req_001",
        reason_or_evidence: "Initial submission",
        event_class: "canonical",
        source_system: "RGP",
        integration_id: null,
        projection_id: null,
        related_entity_type: "request",
        related_entity_id: "req_001",
        lineage: ["request:req_001", "request:req_001"]
      },
      {
        timestamp: "2026-04-02T10:11:00Z",
        actor: "system",
        action: "Observed External State",
        object_type: "projection",
        object_id: "pm_001",
        reason_or_evidence: "Observed external state for request req_001",
        event_class: "federated_sync",
        source_system: "OpenAI Codex",
        integration_id: "int_agent_codex",
        projection_id: "pm_001",
        related_entity_type: "request",
        related_entity_id: "req_001",
        lineage: ["request:req_001", "projection:pm_001", "external:OpenAI Codex", "external_ref:int_agent_codex:request:req_001"]
      }
    ]),
    listWorkflowAnalytics: vi.fn(async () => [{ workflow: "tmpl_assessment", avg_cycle_time: "2.4h", p95_duration: "3.2h", failure_rate: "3%", review_delay: "1.1h", cost_per_execution: "$4.20", trend: "up", federated_projection_count: 3, federated_conflict_count: 1, federated_coverage: "100%" }]),
    listWorkflowTrends: vi.fn(async () => [{ period_start: "2026-04-01", request_count: 4, failed_count: 1, avg_cycle_time_hours: 2.4, review_stale_count: 1, cost_per_execution: 4.2 }]),
    listAgentAnalytics: vi.fn(async () => [{ agent: "OpenAI Codex", invocations: 8, success_rate: "95%", retry_rate: "5%", avg_duration: "3.2m", cost_per_invocation: "$1.50", quality_score: "4.7/5" }]),
    listAgentTrends: vi.fn(async () => [{ period_start: "2026-04-01", invocation_count: 8, retry_rate: 5, success_rate: 95, quality_score: 4.7, avg_duration_minutes: 3.2 }]),
    listDeliveryDoraScoped: vi.fn(async () => [{ scope_type: "team", scope_key: "team_assessment_quality", deployment_frequency: "daily", lead_time_hours: 4.2, change_failure_rate: "3%", mean_time_to_restore_hours: 1.2 }]),
    listDeliveryLifecycleScoped: vi.fn(async () => [{ scope_type: "team", scope_key: "team_assessment_quality", throughput_30d: 14, cycle_time_hours: 4.4, review_time_hours: 1.2, promotion_time_hours: 0.8 }]),
    listDeliveryTrends: vi.fn(async () => [{ period_start: "2026-04-01", throughput_count: 4, completed_count: 3, deployment_count: 2, lead_time_hours: 4.2, failed_count: 1 }]),
    getDeliveryForecast: vi.fn(async () => ({ forecast_days: 14, avg_daily_throughput: 2.1, avg_daily_deployments: 1.2, projected_total_throughput: 29.4, projected_total_deployments: 16.8, projected_lead_time_hours: 4.0 })),
    listDeliveryForecastPoints: vi.fn(async () => [{ period_start: "2026-04-03", projected_throughput_count: 2.1, projected_deployment_count: 1.2, projected_lead_time_hours: 4.0 }]),
    listPerformanceRouteSummaries: vi.fn(async () => ({ items: [{ route: "/api/v1/requests", method: "GET", request_count: 120, avg_duration_ms: 45, p95_duration_ms: 90, error_rate: "1%", apdex: "0.98" }], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    listPerformanceSloSummaries: vi.fn(async () => ({ items: [{ route: "/api/v1/requests", method: "GET", availability_actual: "99.9%", latency_slo_ms: 150, error_budget_remaining: "99%", status: "healthy" }], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    listPerformanceTrends: vi.fn(async () => ({ items: [{ period_start: "2026-04-01", avg_duration_ms: 45, p95_duration_ms: 90, request_count: 120, error_rate: "1%" }], page: 1, page_size: 100, total_count: 1, total_pages: 1 })),
    listPerformanceMetrics: vi.fn(async () => ({ items: [{ route: "/api/v1/requests", method: "GET", correlation_id: "corr_001", trace_id: "trace_001", span_id: "span_001", duration_ms: 45, created_at: "2026-04-02T10:00:00Z" }], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    getPerformanceOperationsSummary: vi.fn(async () => ({ queued_checks: 1, running_checks: 1, waiting_runs: 2, failed_runs: 1, stale_reviews: 1, pending_promotions: 1, avg_check_queue_minutes: 2.5, avg_runtime_queue_minutes: 3.1 })),
    listPerformanceOperationsTrends: vi.fn(async () => [{ period_start: "2026-04-01", queued_checks: 1, running_checks: 1, waiting_runs: 2, failed_runs: 1, stale_reviews: 1, pending_promotions: 1 }]),
    listPortfolios: vi.fn(async () => [portfolio]),
    listTeams: vi.fn(async () => [team]),
    listUsers: vi.fn(async () => [user]),
    listPublicRegistrationOptions: vi.fn(async () => ({
      tenants: [{ id: "tenant_demo", name: "Demo Tenant", status: "active" }],
      organizations: [{ id: "org_assessment", name: "Assessment and Quality", status: "active" }],
      teams: [{ id: "team_assessment_quality", organization_id: "org_assessment", name: "Assessment Quality", kind: "delivery", status: "active" }]
    })),
    listPortfolioSummaries: vi.fn(async () => [{ portfolio_id: "port_assessment", portfolio_name: "Assessment Portfolio", request_count: 12, active_request_count: 3, completed_request_count: 9, deployment_count: 4 }]),
    listBottleneckAnalytics: vi.fn(async () => [{ bottleneck: "review", count: 3, average_delay: "1.2h", severity: "high" }]),
    listAdminUsers: vi.fn(async () => [user, pendingUser]),
    listAdminTenants: vi.fn(async () => [tenant]),
    listAdminOrganizations: vi.fn(async () => [organization]),
    listAdminTeams: vi.fn(async () => [team]),
    listAdminPortfolios: vi.fn(async () => [portfolio]),
    getCurrentPrincipal: vi.fn(async () => ({ user_id: "admin_demo", tenant_id: "tenant_demo", roles: ["platform_admin"] })),
    listPolicies: vi.fn(async () => [{
      id: "pol_001",
      name: "Default Policy",
      status: "active",
      scope: "global",
      owner_team_id: "team_assessment_quality",
      rule_count: 3,
      updated_at: "2026-04-02T10:00:00Z",
      transition_gates: [{ transition_target: "submitted", required_check_name: "Intake Completeness" }],
      rules: ["submitted -> Intake Completeness"],
      review_rules: [{ rule: "required-review" }],
      sla_rules: [{ severity: "high" }]
    }]),
    listIntegrations: vi.fn(async () => [integration]),
    createIntegrationProjection: vi.fn(async () => projection),
    syncIntegrationProjection: vi.fn(async () => projection),
    reconcileIntegration: vi.fn(async () => [reconciliationLog]),
    resolveIntegrationProjection: vi.fn(async () => reconciliationLog),
    updateIntegrationProjectionExternalState: vi.fn(async () => ({
      ...projection,
      external_state: { status: "external_review", title: "External Title" },
      conflicts: [{ field: "status", internal: "awaiting_review", external: "external_review", projection_id: "pm_001" }]
    })),
    listIntegrationProjections: vi.fn(async () => [projection]),
    listIntegrationReconciliationLogs: vi.fn(async () => [reconciliationLog]),
    getPromotion: vi.fn(async () => ({
      id: "pro_001",
      target: "production",
      execution_readiness: "Ready",
      required_checks: [{ name: "policy_pack", state: "passed", severity: "low", detail: "ok", evidence: "evidence", evaluated_by: "system", id: "pchk_001" }],
      required_approvals: [{ reviewer: "ops_isaac", state: "pending", scope: "ops" }],
      check_results: [{ id: "pchk_001", name: "policy_pack", state: "passed", severity: "low", detail: "ok", evidence: "evidence", evaluated_by: "system" }],
      check_runs: [{ id: "pcr_001", scope: "promotion", status: "completed", trigger_reason: "authorize", enqueued_by: "system", queued_at: "2026-04-02T10:00:00Z" }],
      overrides: [{ check_result_id: "pchk_001", state: "approved", reason: "manual override", requested_by: "ops_isaac", decided_by: "ops_isaac", created_at: "2026-04-02T10:05:00Z" }],
      deployment_executions: [{ executed_at: "2026-04-02T10:10:00Z", target: "production", integration_id: "int_ms_foundry", status: "completed", external_reference: "dep_001", detail: "ok" }],
      promotion_history: [{ timestamp: "2026-04-02T10:10:00Z", actor: "ops_isaac", action: "executed" }]
    }))
  };
});

vi.mock("./requests/[requestId]/agents/[sessionId]/live-session", () => ({
  AgentSessionLiveView: ({
    initialSession,
    initialContext,
  }: {
    initialSession: { summary: string };
    initialContext: { bundle: { id: string; contents?: Record<string, unknown> } };
  }) => (
    <div>
      Live Session: {initialSession.summary} / {initialContext.bundle.id}
      {"knowledge_context" in (initialContext.bundle.contents ?? {}) ? (
        <div>Knowledge: {String(((initialContext.bundle.contents as Record<string, unknown>).knowledge_context as Array<Record<string, unknown>>)?.[0]?.name ?? "none")}</div>
      ) : null}
    </div>
  )
}));

describe("coverage smoke pages", () => {
  it("renders analytics pages", async () => {
    render(await AnalyticsPage());
    expect(screen.getByText("Analytics Overview")).toBeInTheDocument();
    expect(screen.getByText("Delivery and Workflow Volume")).toBeInTheDocument();

    render(await WorkflowAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Workflow Analytics")).toBeInTheDocument();
    expect(screen.getByText("Workflow Volume")).toBeInTheDocument();
    expect(screen.getByText("3 projections")).toBeInTheDocument();
    expect(screen.getByText("100% coverage")).toBeInTheDocument();
    expect(screen.getByText("View federated conflicts")).toBeInTheDocument();
    expect(screen.getByText("Open federation control")).toBeInTheDocument();

    render(
      await WorkflowFederationPage({
        params: Promise.resolve({ workflow: "tmpl_assessment" }),
        searchParams: Promise.resolve({ days: "30", federation: "with_conflict" })
      })
    );
    expect(screen.getByText("tmpl_assessment Federation")).toBeInTheDocument();
    expect(screen.getAllByText("Conflict Focus").length).toBeGreaterThan(0);
    expect(screen.getByText("Affected Requests")).toBeInTheDocument();
    expect(screen.getByText("Affected Runs")).toBeInTheDocument();
    expect(screen.getAllByText("Open request").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Open history").length).toBeGreaterThan(0);

    render(await WorkflowHistoryPage({ params: Promise.resolve({ workflow: "tmpl_assessment" }), searchParams: Promise.resolve({ event_class: "federated_resolution" }) }));
    expect(screen.getByText("tmpl_assessment History")).toBeInTheDocument();
    expect(screen.getByText("Merge")).toBeInTheDocument();
    expect(screen.getByText("workflow:tmpl_assessment -> request:req_001 -> projection:pm_001")).toBeInTheDocument();

    render(await AgentAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Agent Analytics")).toBeInTheDocument();
    expect(screen.getByText("Agent Invocation Trend")).toBeInTheDocument();

    render(await DeliveryAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Delivery Analytics")).toBeInTheDocument();
    expect(screen.getByText("Forecast Throughput and Deployments")).toBeInTheDocument();

    render(await PerformanceAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Performance Analytics")).toBeInTheDocument();
    expect(screen.getByText("Queue Pressure")).toBeInTheDocument();

    render(await AnalyticsCostPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Cost Analytics")).toBeInTheDocument();
    expect(screen.getByText("Estimated Spend Over Time")).toBeInTheDocument();

    render(await BottleneckAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Bottleneck Analytics")).toBeInTheDocument();
  });

  it("renders help pages", async () => {
    render(await HelpOverviewPage());
    expect(screen.getByText("Help and User Guide")).toBeInTheDocument();
    expect(screen.getByText("Guide Map")).toBeInTheDocument();

    render(await HelpRequestsPage());
    expect(screen.getByText("Help: Requests")).toBeInTheDocument();
    expect(screen.getByText("Create Request Form")).toBeInTheDocument();

    render(await HelpOperationsPage());
    expect(screen.getByText("Help: Operations")).toBeInTheDocument();
    expect(screen.getByText("Operational Areas")).toBeInTheDocument();

    render(await HelpAdminPage());
    expect(screen.getByText("Help: Admin")).toBeInTheDocument();
    expect(screen.getByText("Admin Areas")).toBeInTheDocument();

    render(await HelpAnalyticsPage());
    expect(screen.getByText("Help: Analytics")).toBeInTheDocument();
    expect(screen.getByText("Analytics Pages")).toBeInTheDocument();

    render(await HelpJourneysPage());
    expect(screen.getByText("Help: User Journeys")).toBeInTheDocument();
    expect(screen.getByText("Supported User Journeys")).toBeInTheDocument();
  });

  it("renders forbidden access handling", async () => {
    render(await ForbiddenPage({ searchParams: Promise.resolve({ from: "/api/v1/admin/templates" }) }));
    expect(screen.getByRole("heading", { name: "Access Restricted" })).toBeInTheDocument();
    expect(screen.getByText("/api/v1/admin/templates")).toBeInTheDocument();
  });

  it("renders request agent assignment preview", async () => {
    render(
      await RequestAgentsPage({
        params: Promise.resolve({ requestId: "req_001" }),
        searchParams: Promise.resolve({
          integration: "int_agent_codex",
          collaboration_mode: "agent_assisted",
          agent_operating_profile: "review",
        }),
      })
    );
    expect(screen.getByText("Governed Assignment Preview")).toBeInTheDocument();
    expect(screen.getByText("request.summary")).toBeInTheDocument();
    expect(screen.getByText("Refresh Preview")).toBeInTheDocument();
    expect(screen.getByText(/Mode: agent_assisted · Profile: review/)).toBeInTheDocument();
    expect(screen.getByText("Reusable Governed Knowledge")).toBeInTheDocument();
  });

  it("renders request agent session page with governed context", async () => {
    render(await RequestAgentSessionPage({ params: Promise.resolve({ requestId: "req_001", sessionId: "ags_001" }) }));
    expect(screen.getByText(/Live Session:/)).toBeInTheDocument();
    expect(screen.getByText(/cb_001/)).toBeInTheDocument();
    expect(screen.getByText(/Knowledge:/)).toBeInTheDocument();
  });

  it("renders the public registration page", async () => {
    render(await RegisterPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByText("Create Account Request")).toBeInTheDocument();
    expect(screen.getByText("Requested Access")).toBeInTheDocument();
    expect(screen.getByText("Tenant")).toBeInTheDocument();
    expect(screen.getByText("Organization")).toBeInTheDocument();
    expect(screen.getByText("Requested Team")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Assessment and Quality")).toBeInTheDocument();
  });

  it("renders request pages", async () => {
    render(await RequestDetailPage({ params: Promise.resolve({ requestId: "req_001" }), searchParams: Promise.resolve({}) }));
    expect(screen.getByText("Request Detail")).toBeInTheDocument();
    expect(screen.getByText("Assign to Agent")).toBeInTheDocument();
    expect(screen.getAllByText("Governed Knowledge").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Assessment Review Playbook").length).toBeGreaterThan(0);
    expect(screen.getByText("Routing Recommendation")).toBeInTheDocument();
    expect(screen.getAllByText("Assessment Reviewers").length).toBeGreaterThan(0);
    expect(screen.getByText("Federated Projections")).toBeInTheDocument();
    expect(screen.getByText("status: canonical awaiting_review / external external_review")).toBeInTheDocument();
    expect(screen.getByText("Adapter openai_projection via adapter:openai_projection")).toBeInTheDocument();

    render(await RequestAgentsPage({ params: Promise.resolve({ requestId: "req_001" }), searchParams: Promise.resolve({}) }));
    expect(screen.getAllByText("Agent Sessions").length).toBeGreaterThan(0);

    render(await RequestFederatedConflictsPage());
    expect(screen.getAllByText("Federated Conflicts").length).toBeGreaterThan(0);
    expect(screen.getByText("1 projection • 1 conflict")).toBeInTheDocument();
    expect(screen.getAllByText("Open request").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Open history").length).toBeGreaterThan(0);

    render(await RequestHistoryPage({ params: Promise.resolve({ requestId: "req_001" }), searchParams: Promise.resolve({ event_class: "federated_sync" }) }));
    expect(screen.getByText("Audit History")).toBeInTheDocument();
    expect(screen.getByText("Observed External State")).toBeInTheDocument();
    expect(screen.getByText("federated sync")).toBeInTheDocument();
    expect(screen.getAllByText("OpenAI Codex").length).toBeGreaterThan(0);
    expect(screen.getByText("request:req_001 -> projection:pm_001 -> external:OpenAI Codex -> external_ref:int_agent_codex:request:req_001")).toBeInTheDocument();
    expect(screen.getAllByText("Federated Sync").length).toBeGreaterThan(0);

    render(await RequestProjectionPage({ params: Promise.resolve({ requestId: "req_001", projectionId: "pm_001" }) }));
    expect(screen.getByText("Projection Detail")).toBeInTheDocument();
    expect(screen.getByText("Remediation Controls")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "resume_session" })).toBeInTheDocument();

    render(await RequestAgentSessionPage({ params: Promise.resolve({ requestId: "req_001", sessionId: "ags_001" }) }));
    expect(screen.getByText("Agent Session: Codex")).toBeInTheDocument();
    expect(screen.getByText("Live Session: Proposed an updated assessment outline. / cb_001")).toBeInTheDocument();
  });

  it("renders admin pages", async () => {
    render(await ReviewQueuePage({ searchParams: Promise.resolve({ request_id: "req_001" }) }));
    expect(screen.getByText("Routing Recommendation for req_001")).toBeInTheDocument();
    expect(screen.getByText("Governed Knowledge for req_001")).toBeInTheDocument();
    expect(screen.getByText("Published guidance retrieved for the currently filtered request.")).toBeInTheDocument();

    render(await AdminOrgPage());
    expect(screen.getByText("Admin Organization")).toBeInTheDocument();
    expect(screen.getByText("Tenants, Organizations, Teams, and Members")).toBeInTheDocument();
    expect(screen.getByText("Demo Tenant")).toBeInTheDocument();
    expect(screen.getByText("Create Tenant")).toBeInTheDocument();
    expect(screen.getByText("Assessment and Quality")).toBeInTheDocument();
    expect(screen.getByText("Unassigned Users")).toBeInTheDocument();
    expect(screen.getByText("Pending User")).toBeInTheDocument();
    expect(screen.getByText("pending_activation")).toBeInTheDocument();

    render(await AdminTeamDetailPage({ params: Promise.resolve({ teamId: "team_assessment_quality" }) }));
    expect(screen.getByText("Team Settings")).toBeInTheDocument();
    expect(screen.getByText("Create User In Team")).toBeInTheDocument();

    render(await AdminUserDetailPage({ params: Promise.resolve({ userId: "user_demo" }) }));
    expect(screen.getByText("User Settings")).toBeInTheDocument();

    render(await AdminIntegrationsPage());
    expect(screen.getByText("Admin Integrations")).toBeInTheDocument();

    render(await AdminDomainPacksPage());
    expect(screen.getByText("Admin Domain Packs")).toBeInTheDocument();
    expect(screen.getByText("Create Domain Pack")).toBeInTheDocument();
    expect(screen.getAllByText("Content and Editorial Pack").length).toBeGreaterThan(0);

    render(await AdminDomainPackDetailPage({ params: Promise.resolve({ packId: "dp_001" }) }));
    expect(screen.getByRole("heading", { name: "Content and Editorial Pack" })).toBeInTheDocument();
    expect(screen.getByText("Activate Pack")).toBeInTheDocument();
    expect(screen.getByText("Install Pack")).toBeInTheDocument();
    expect(screen.getByText("Validation")).toBeInTheDocument();
    expect(screen.getByText("Pack contributions satisfy the current governance checks.")).toBeInTheDocument();
    expect(screen.getByText("Version Comparison")).toBeInTheDocument();
    expect(screen.getByText("Compared with 0.9.0: 2 additions and 1 removals across declared contributions.")).toBeInTheDocument();
    expect(screen.getByText("Version Lineage")).toBeInTheDocument();
    expect(screen.getAllByText("0.9.0").length).toBeGreaterThan(0);

    render(await AdminIntegrationDetailPage({ params: Promise.resolve({ integrationId: "int_agent_codex" }) }));
    expect(screen.getByText("Integration Settings")).toBeInTheDocument();
    expect(screen.getByText("Provider Settings")).toBeInTheDocument();
    expect(screen.getByText("Projection Mappings")).toBeInTheDocument();
    expect(screen.getByText("Federation Controls")).toBeInTheDocument();
    expect(screen.getByText("Reconciliation Activity")).toBeInTheDocument();
    expect(screen.getByText("Record External State")).toBeInTheDocument();
    expect(screen.getAllByText("Adapter openai_projection via adapter:openai_projection").length).toBeGreaterThan(0);
    expect(screen.getByText(/Resolution guidance:/)).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "resume_session" })).toBeInTheDocument();
    expect(screen.getByText("Clear stored API key")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("sk-test")).not.toBeInTheDocument();

    render(await AdminPoliciesPage());
    expect(screen.getByText("Admin Policies")).toBeInTheDocument();
  });

  it("renders execution and governance pages", async () => {
    render(await RunsPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Runs" })).toBeInTheDocument();
    expect(screen.getByText("All Runs")).toBeInTheDocument();
    expect(screen.getByText("1 projection")).toBeInTheDocument();
    expect(screen.getAllByText("1 conflict").length).toBeGreaterThan(0);
    expect(screen.getByText("Federated Conflicts")).toBeInTheDocument();
    expect(screen.getByText("Open remediation")).toBeInTheDocument();
    expect(screen.getAllByText("Sync").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Resume Session").length).toBeGreaterThan(0);

    render(await FailedRunsPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Failed Runs" })).toBeInTheDocument();

    render(await RunDetailPage({ params: Promise.resolve({ runId: "run_001" }) }));
    expect(screen.getByText("Run Detail")).toBeInTheDocument();
    expect(screen.getByText("Federated Execution")).toBeInTheDocument();
    expect(screen.getAllByText("Adapter openai_projection via adapter:openai_projection").length).toBeGreaterThan(0);

    render(await RunHistoryPage({ params: Promise.resolve({ runId: "run_001" }), searchParams: Promise.resolve({ event_class: "federated_sync" }) }));
    expect(screen.getByText("Run History")).toBeInTheDocument();
    expect(screen.getAllByText("Observed External State").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Federated Sync").length).toBeGreaterThan(0);

    render(await PromotionPendingPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Promotion Pending" })).toBeInTheDocument();

    render(await PromotionPage({ params: Promise.resolve({ promotionId: "pro_001" }) }));
    expect(screen.getByRole("heading", { level: 1, name: "Promotion Gate" })).toBeInTheDocument();
    expect(screen.queryByText("No promotion history.")).not.toBeInTheDocument();

    render(await ArtifactsPage());
    expect(screen.getByRole("heading", { name: "Artifacts" })).toBeInTheDocument();

    render(await ArtifactDetailPage({ params: Promise.resolve({ artifactId: "art_001" }) }));
    expect(screen.getByText("Artifact Detail")).toBeInTheDocument();

    render(await KnowledgePage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Knowledge" })).toBeInTheDocument();
    expect(screen.getByText("Assessment Review Playbook")).toBeInTheDocument();

    render(await NewKnowledgeArtifactPage());
    expect(screen.getByRole("heading", { name: "New Knowledge Artifact" })).toBeInTheDocument();
    expect(screen.getByText("Create Knowledge Artifact")).toBeInTheDocument();

    render(await KnowledgeArtifactDetailPage({ params: Promise.resolve({ artifactId: "ka_001" }) }));
    expect(screen.getByRole("heading", { name: "Assessment Review Playbook" })).toBeInTheDocument();
    expect(screen.getByText("Published guidance")).toBeInTheDocument();

    render(await PlanningPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Planning" })).toBeInTheDocument();
    expect(screen.getAllByText("Assessment Quality Initiative").length).toBeGreaterThan(0);
    expect(screen.getByText("50% complete")).toBeInTheDocument();
    expect(screen.getByText("on track")).toBeInTheDocument();
    expect(screen.getByText("Roadmap Health")).toBeInTheDocument();
    expect(screen.getByText("Due Soon")).toBeInTheDocument();

    render(await NewPlanningConstructPage());
    expect(screen.getByRole("heading", { name: "New Planning Construct" })).toBeInTheDocument();
    expect(screen.getByText("Create Planning Construct")).toBeInTheDocument();

    render(await PlanningConstructDetailPage({ params: Promise.resolve({ constructId: "pc_001" }) }));
    expect(screen.getByRole("heading", { name: "Assessment Quality Initiative" })).toBeInTheDocument();
    expect(screen.getByText("Add Request to Construct")).toBeInTheDocument();
    expect(screen.getByText("Progress Breakdown")).toBeInTheDocument();
    expect(screen.getAllByText("Save").length).toBeGreaterThan(0);
    expect(screen.getByText("Move Earlier")).toBeInTheDocument();
    expect(screen.getByText("Move Later")).toBeInTheDocument();
    expect(screen.getByText("Remove")).toBeInTheDocument();

    render(await QueuesPage());
    expect(screen.getByRole("heading", { name: "Queues" })).toBeInTheDocument();
    expect(screen.getByText("Assessment Reviewers")).toBeInTheDocument();
    expect(screen.getByText("Assessment Review SLA")).toBeInTheDocument();
    expect(screen.getByText("Stale Review Escalation")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Notify Queue Lead" }).length).toBeGreaterThan(0);

    render(await SlaRiskRequestsPage());
    expect(screen.getByRole("heading", { name: "SLA Risk" })).toBeInTheDocument();
    expect(screen.getByText("review • 11h / 8h")).toBeInTheDocument();
    expect(screen.getAllByText("Stale Review Escalation").length).toBeGreaterThan(0);
    expect(screen.getByText("Pending operator action")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Notify Queue Lead" }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: "Execute Escalation" }).length).toBeGreaterThan(0);

    render(await CapabilitiesPage());
    expect(screen.getByRole("heading", { name: "Capability Registry" })).toBeInTheDocument();

    render(await CapabilityDetailPage({ params: Promise.resolve({ capabilityId: "cap_001" }) }));
    expect(screen.getByText("Capability Detail")).toBeInTheDocument();
  });
});
