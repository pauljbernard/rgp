export const requestStatuses = [
  "draft",
  "submitted",
  "validation_failed",
  "validated",
  "classified",
  "ownership_resolved",
  "planned",
  "queued",
  "in_execution",
  "awaiting_input",
  "awaiting_review",
  "under_review",
  "changes_requested",
  "approved",
  "rejected",
  "promotion_pending",
  "promoted",
  "completed",
  "failed",
  "canceled",
  "archived"
] as const;

export const requestPriorities = ["low", "medium", "high", "urgent"] as const;
export const runStatuses = ["queued", "running", "waiting", "failed", "completed", "paused"] as const;
export const capabilityStatuses = ["active", "pending", "deprecated"] as const;

export type RequestStatus = (typeof requestStatuses)[number];
export type RequestPriority = (typeof requestPriorities)[number];
export type RunStatus = (typeof runStatuses)[number];
export type CapabilityStatus = (typeof capabilityStatuses)[number];

export type PairValue = [string, string];

export type RequestRecord = {
  id: string;
  tenant_id: string;
  request_type: string;
  template_id: string;
  template_version: string;
  title: string;
  summary: string;
  status: RequestStatus;
  priority: RequestPriority;
  sla_policy_id: string | null;
  submitter_id: string;
  owner_team_id: string | null;
  owner_user_id: string | null;
  workflow_binding_id: string | null;
  current_run_id: string | null;
  policy_context: Record<string, unknown>;
  input_payload: Record<string, unknown>;
  tags: string[];
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
  version: number;
  is_archived: boolean;
  sla_risk_level: string | null;
  sla_risk_reason: string | null;
  federated_projection_count: number;
  federated_conflict_count: number;
};

export type RequestDetail = {
  request: RequestRecord;
  latest_run_id: string | null;
  latest_artifact_ids: string[];
  active_blockers: string[];
  check_results: CheckResult[];
  check_runs: CheckRunRecord[];
  agent_sessions: AgentSessionRecord[];
  next_required_action: string;
  predecessors: RequestRelationship[];
  successors: RequestRelationship[];
};

export type RequestRelationship = {
  request_id: string;
  relationship_type: string;
};

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
};

export type TemplateRecord = {
  id: string;
  version: string;
  name: string;
  description: string;
  status: "draft" | "published" | "deprecated";
  schema: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TemplateValidationIssue = {
  level: string;
  path: string;
  message: string;
};

export type TemplateValidationPreviewField = {
  key: string;
  title: string;
  field_type: string;
  required: boolean;
  default?: unknown;
  enum_values: string[];
  description?: string | null;
};

export type TemplateValidationPreview = {
  field_count: number;
  required_fields: string[];
  conditional_rule_count: number;
  routing_rule_count: number;
  artifact_type_count: number;
  check_requirement_count: number;
  promotion_requirement_count: number;
  routed_fields: string[];
  fields: TemplateValidationPreviewField[];
};

export type TemplateValidationResult = {
  valid: boolean;
  issues: TemplateValidationIssue[];
  preview: TemplateValidationPreview;
};

export type RunRecord = {
  id: string;
  request_id: string;
  workflow: string;
  status: RunStatus;
  current_step: string;
  elapsed_time: string;
  waiting_reason: string | null;
  updated_at: string;
  owner_team: string;
  federated_projection_count: number;
  federated_conflict_count: number;
};

export type RunStep = {
  id: string;
  name: string;
  status: "completed" | "active" | "blocked" | "failed" | "pending";
  owner: string;
  started_at?: string | null;
  ended_at?: string | null;
};

export type RuntimeDispatchRecord = {
  id: string;
  run_id: string;
  request_id: string;
  integration_id: string;
  dispatch_type: string;
  status: string;
  external_reference?: string | null;
  detail: string;
  payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  dispatched_at: string;
};

export type RuntimeSignalRecord = {
  event_id: string;
  source: string;
  status: string;
  current_step?: string | null;
  detail: string;
  payload: Record<string, unknown>;
  received_at: string;
};

export type RunCommand = "Pause" | "Resume" | "Retry Step" | "Cancel Run";

export type RunDetail = RunRecord & {
  workflow_identity: string;
  progress_percent: number;
  current_step_input_summary: string;
  current_step_output_summary: string;
  failure_reason?: string | null;
  command_surface: string[];
  steps: RunStep[];
  run_context: PairValue[];
  conversation_thread_id: string;
  runtime_dispatches: RuntimeDispatchRecord[];
  runtime_signals: RuntimeSignalRecord[];
  federated_projections: ProjectionMappingRecord[];
};

export type ArtifactRecord = {
  id: string;
  type: string;
  name: string;
  current_version: string;
  status: string;
  request_id: string;
  updated_at: string;
  owner: string;
  review_state: string;
  promotion_relevant: boolean;
};

export type ArtifactVersion = {
  id: string;
  label: string;
  status: string;
  created_at: string;
  author: string;
  summary: string;
  content: string;
};

export type ArtifactDetail = {
  artifact: ArtifactRecord;
  versions: ArtifactVersion[];
  selected_version_id: string;
  review_state: "approved" | "changes_requested" | "blocked" | "commented" | "pending";
  stale_review: boolean;
  history: ArtifactEvent[];
  lineage: ArtifactLineageEdge[];
};

export type ArtifactEvent = {
  timestamp: string;
  actor: string;
  action: string;
  detail: string;
  artifact_version_id: string | null;
};

export type ArtifactLineageEdge = {
  from_version_id: string | null;
  to_version_id: string;
  relation: string;
  created_at: string;
};

export type KnowledgeArtifactRecord = {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  content: string | null;
  content_type: string;
  version: number;
  status: string;
  policy_scope: Record<string, unknown> | null;
  provenance: Array<Record<string, unknown>>;
  tags: string[];
  created_by: string;
  created_at: string | null;
  updated_at: string | null;
};

export type KnowledgeVersionRecord = {
  id: string;
  artifact_id: string;
  version: number;
  content: string | null;
  summary: string | null;
  author: string;
  created_at: string | null;
};

export type PlanningConstructRecord = {
  id: string;
  tenant_id: string;
  type: string;
  name: string;
  description: string | null;
  owner_team_id: string | null;
  status: string;
  priority: number;
  target_date: string | null;
  capacity_budget: number | null;
  created_at: string | null;
  updated_at: string | null;
};

export type PlanningMembershipRecord = {
  id: string;
  planning_construct_id: string;
  request_id: string;
  sequence: number;
  priority: number;
  added_at: string | null;
};

export type PlanningProgressRecord = {
  construct_id: string;
  total: number;
  status_counts: Record<string, number>;
  completion_pct: number;
};

export type PlanningRoadmapEntry = {
  id: string;
  type: string;
  name: string;
  status: string;
  priority: number;
  target_date: string | null;
  capacity_budget: number | null;
  member_count: number;
  completion_pct: number;
  completed_count: number;
  in_progress_count: number;
  blocked_count: number;
  schedule_state: string;
  owner_team_id: string | null;
};

export type PlanningConstructDetail = {
  construct: PlanningConstructRecord;
  memberships: PlanningMembershipRecord[];
  progress: PlanningProgressRecord;
};

export type DomainPackRecord = {
  id: string;
  tenant_id: string;
  name: string;
  version: string;
  description: string | null;
  status: string;
  contributed_templates: string[];
  contributed_artifact_types: string[];
  contributed_workflows: string[];
  contributed_policies: string[];
  activated_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type DomainPackInstallation = {
  id: string;
  tenant_id: string;
  pack_id: string;
  installed_version: string;
  status: string;
  installed_by: string;
  installed_at: string | null;
};

export type DomainPackDetail = {
  pack: DomainPackRecord;
  installations: DomainPackInstallation[];
};

export type DomainPackContributionDelta = {
  category: string;
  added: string[];
  removed: string[];
};

export type DomainPackComparison = {
  current_pack_id: string;
  current_version: string;
  baseline_pack_id: string | null;
  baseline_version: string | null;
  deltas: DomainPackContributionDelta[];
  summary: string;
};

export type DomainPackLineageEntry = {
  pack_id: string;
  version: string;
  status: string;
  created_at: string | null;
  activated_at: string | null;
  contribution_count: number;
};

export type AssignmentGroupRecord = {
  id: string;
  tenant_id: string;
  name: string;
  skill_tags: string[];
  max_capacity: number | null;
  current_load: number;
  status: string;
  created_at: string | null;
};

export type EscalationRuleRecord = {
  id: string;
  tenant_id: string;
  name: string;
  condition: Record<string, unknown>;
  escalation_target: string;
  escalation_type: string;
  delay_minutes: number;
  status: string;
  created_at: string | null;
};

export type EscalationExecutionRecord = {
  request_id: string;
  rule_id: string;
  escalation_type: string;
  escalation_target: string;
  outcome: string;
  executed_at: string | null;
};

export type SlaDefinitionRecord = {
  id: string;
  tenant_id: string;
  name: string;
  scope_type: string;
  scope_id: string | null;
  response_target_hours: number | null;
  resolution_target_hours: number | null;
  review_deadline_hours: number | null;
  warning_threshold_pct: number;
  status: string;
  created_at: string | null;
};

export type SlaBreachAuditRecord = {
  id: string;
  tenant_id: string;
  sla_definition_id: string;
  request_id: string;
  breach_type: string;
  target_hours: number;
  actual_hours: number;
  severity: string;
  remediation_action: string | null;
  breached_at: string | null;
};

export type RemediateSlaBreachRequest = {
  remediation_action: string;
};

export type RoutingRecommendationRecord = {
  request_id: string;
  recommended_group_id: string | null;
  recommended_group_name: string | null;
  matched_skills: string[];
  route_basis: string[];
  current_load: number | null;
  max_capacity: number | null;
  sla_status: string;
  escalation_targets: string[];
};

export type ReviewQueueItem = {
  id: string;
  request_id: string;
  review_scope: string;
  artifact_or_changeset: string;
  type: string;
  priority: RequestPriority;
  sla: string;
  blocking_status: string;
  assigned_reviewer: string;
  stale: boolean;
};

export type ReviewDecision = "approve" | "changes_requested";
export type PromotionAction = "dry_run" | "authorize" | "execute";

export type PromotionCheck = {
  name: string;
  state: string;
  detail: string;
};

export type CheckResult = {
  id: string;
  request_id: string;
  promotion_id: string | null;
  name: string;
  state: string;
  detail: string;
  severity: string;
  evidence: string;
  evaluated_at: string;
  evaluated_by: string;
};

export type CheckRunRecord = {
  id: string;
  request_id: string;
  promotion_id: string | null;
  scope: "request" | "promotion";
  status: "queued" | "running" | "completed" | "failed";
  trigger_reason: string;
  enqueued_by: string;
  worker_task_id: string | null;
  error_message: string | null;
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type CheckOverride = {
  id: string;
  check_result_id: string;
  request_id: string;
  promotion_id: string | null;
  state: string;
  reason: string;
  requested_by: string;
  decided_by: string;
  created_at: string;
  decided_at: string;
};

export type PromotionApproval = {
  reviewer: string;
  state: string;
  scope: string;
};

export type PromotionHistoryEntry = {
  timestamp: string;
  actor: string;
  action: string;
};

export type DeploymentExecutionRecord = {
  id: string;
  promotion_id: string;
  request_id: string;
  integration_id: string;
  target: string;
  strategy: string;
  status: string;
  external_reference?: string | null;
  detail: string;
  payload: Record<string, unknown>;
  response_payload: Record<string, unknown>;
  executed_at: string;
};

export type PromotionDetail = {
  id: string;
  request_id: string;
  target: string;
  strategy: string;
  required_checks: PromotionCheck[];
  check_results: CheckResult[];
  check_runs: CheckRunRecord[];
  overrides: CheckOverride[];
  required_approvals: PromotionApproval[];
  stale_warnings: string[];
  execution_readiness: string;
  deployment_executions: DeploymentExecutionRecord[];
  promotion_history: PromotionHistoryEntry[];
};

export type CapabilityRecord = {
  id: string;
  name: string;
  type: string;
  version: string;
  status: CapabilityStatus;
  owner: string;
  updated_at: string;
  usage_count: number;
};

export type CapabilityDetail = {
  capability: CapabilityRecord;
  definition: string;
  lineage: string[];
  usage: PairValue[];
  performance: PairValue[];
  history: PromotionHistoryEntry[];
};

export type AnalyticsWorkflowRow = {
  workflow: string;
  avg_cycle_time: string;
  p95_duration: string;
  failure_rate: string;
  review_delay: string;
  cost_per_execution: string;
  trend: string;
  federated_projection_count: number;
  federated_conflict_count: number;
  federated_coverage: string;
};

export type AnalyticsAgentRow = {
  agent: string;
  invocations: number;
  success_rate: string;
  retry_rate: string;
  avg_duration: string;
  cost_per_invocation: string;
  quality_score: string;
};

export type AnalyticsBottleneckRow = {
  workflow: string;
  step: string;
  avg_wait_time: string;
  block_count: number;
  reviewer_delay: string;
  trend: string;
};

export type WorkflowTrendPoint = {
  period_start: string;
  request_count: number;
  failed_count: number;
  avg_cycle_time_hours: number;
  review_stale_count: number;
  cost_per_execution: number;
};

export type AgentTrendPoint = {
  period_start: string;
  invocation_count: number;
  success_rate: number;
  retry_rate: number;
  avg_duration_minutes: number;
  quality_score: number;
};

export type UserRecord = {
  id: string;
  tenant_id: string;
  display_name: string;
  email: string;
  role_summary: string[];
  status: string;
  has_password: boolean;
  password_reset_required: boolean;
  registration_request_id?: string | null;
};

export type TenantRecord = {
  id: string;
  name: string;
  status: string;
  organization_count: number;
};

export type OrganizationRecord = {
  id: string;
  tenant_id: string;
  name: string;
  status: string;
};

export type TeamMemberRecord = {
  user_id: string;
  display_name: string;
  email: string;
  role: string;
};

export type TeamRecord = {
  id: string;
  tenant_id: string;
  organization_id: string;
  organization_name: string;
  name: string;
  kind: string;
  status: string;
  member_count: number;
  members: TeamMemberRecord[];
};

export type PortfolioRecord = {
  id: string;
  tenant_id: string;
  name: string;
  status: string;
  owner_team_id: string;
  scope_keys: string[];
};

export type PublicTenantOption = {
  id: string;
  name: string;
  status: string;
};

export type PublicOrganizationOption = {
  id: string;
  name: string;
  status: string;
};

export type PublicTeamOption = {
  id: string;
  organization_id: string;
  name: string;
  kind: string;
  status: string;
};

export type RegistrationOptions = {
  tenants: PublicTenantOption[];
  organizations: PublicOrganizationOption[];
  teams: PublicTeamOption[];
};

export type PortfolioSummary = {
  portfolio_id: string;
  portfolio_name: string;
  owner_team_id: string;
  team_count: number;
  member_count: number;
  request_count: number;
  active_request_count: number;
  completed_request_count: number;
  deployment_count: number;
};

export type CreateUserInput = {
  id: string;
  display_name: string;
  email: string;
  role_summary?: string[];
  status?: string;
  password?: string;
  password_reset_required?: boolean;
  registration_request_id?: string | null;
};

export type UpdateUserInput = {
  display_name: string;
  email: string;
  role_summary?: string[];
  status?: string;
  password?: string;
  password_reset_required?: boolean | null;
  reset_password?: boolean;
};

export type CreateTeamInput = {
  id: string;
  organization_id: string;
  name: string;
  kind?: string;
  status?: string;
};

export type UpdateTeamInput = {
  organization_id: string;
  name: string;
  kind?: string;
  status?: string;
};

export type CreateOrganizationInput = {
  id: string;
  tenant_id?: string | null;
  name: string;
  status?: string;
};

export type CreateTenantInput = {
  id: string;
  name: string;
  status?: string;
};

export type UpdateTenantInput = {
  name: string;
  status?: string;
};

export type Principal = {
  user_id: string;
  tenant_id: string;
  roles: string[];
};

export type UpdateOrganizationInput = {
  name: string;
  status?: string;
};

export type AddTeamMembershipInput = {
  team_id: string;
  user_id: string;
  role?: string;
};

export type CreatePortfolioInput = {
  id: string;
  name: string;
  owner_team_id: string;
  scope_keys?: string[];
  status?: string;
};

export type DeliveryDoraRow = {
  scope_type: string;
  scope_key: string;
  deployment_frequency: string;
  lead_time_hours: number;
  change_failure_rate: string;
  mean_time_to_restore_hours: number;
};

export type DeliveryLifecycleRow = {
  scope_type: string;
  scope_key: string;
  throughput_30d: number;
  lead_time_hours: number;
  cycle_time_hours: number;
  execution_time_hours: number;
  queue_time_hours: number;
  review_time_hours: number;
  approval_time_hours: number;
  promotion_time_hours: number;
};

export type DeliveryTrendPoint = {
  period_start: string;
  completed_count: number;
  failed_count: number;
  deployment_count: number;
  throughput_count: number;
  lead_time_hours: number;
};

export type DeliveryForecastPoint = {
  period_start: string;
  projected_throughput_count: number;
  projected_deployment_count: number;
  projected_lead_time_hours: number;
};

export type DeliveryForecastSummary = {
  forecast_days: number;
  avg_daily_throughput: number;
  avg_daily_deployments: number;
  projected_total_throughput: number;
  projected_total_deployments: number;
  projected_lead_time_hours: number;
};

export type PerformanceRouteSummary = {
  route: string;
  method: string;
  request_count: number;
  error_rate: string;
  avg_duration_ms: number;
  p95_duration_ms: number;
  apdex: string;
};

export type PerformanceSloSummary = {
  route: string;
  method: string;
  availability_slo: string;
  latency_slo_ms: number;
  availability_actual: string;
  p95_duration_ms: number;
  status: string;
  error_budget_remaining: string;
};

export type PerformanceMetricRecord = {
  id: number;
  route: string;
  method: string;
  status_code: number;
  duration_ms: number;
  trace_id?: string | null;
  span_id?: string | null;
  correlation_id?: string | null;
  occurred_at: string;
};

export type PerformanceTrendPoint = {
  period_start: string;
  route: string;
  method: string;
  request_count: number;
  avg_duration_ms: number;
  p95_duration_ms: number;
  error_rate: string;
};

export type PerformanceOperationsSummary = {
  queued_checks: number;
  running_checks: number;
  waiting_runs: number;
  failed_runs: number;
  stale_reviews: number;
  pending_promotions: number;
  avg_check_queue_minutes: number;
  avg_runtime_queue_minutes: number;
};

export type PerformanceOperationsTrendPoint = {
  period_start: string;
  queued_checks: number;
  running_checks: number;
  waiting_runs: number;
  failed_runs: number;
  stale_reviews: number;
  pending_promotions: number;
};

export type AuditEntry = {
  timestamp: string;
  actor: string;
  action: string;
  object_type: string;
  object_id: string;
  reason_or_evidence: string;
  event_class: string;
  source_system?: string | null;
  integration_id?: string | null;
  projection_id?: string | null;
  related_entity_type?: string | null;
  related_entity_id?: string | null;
  lineage: string[];
};

export type PolicyRecord = {
  id: string;
  name: string;
  status: string;
  scope: string;
  rules: string[];
  transition_gates: PolicyGateRule[];
  updated_at: string;
};

export type PolicyGateRule = {
  transition_target: string;
  required_check_name: string;
};

export type IntegrationRecord = {
  id: string;
  name: string;
  type: string;
  status: string;
  endpoint: string;
  settings: Record<string, unknown>;
  has_api_key?: boolean;
  has_access_token?: boolean;
  resolved_endpoint?: string | null;
  supports_direct_assignment?: boolean;
  supports_interactive_sessions?: boolean;
  provider?: string | null;
};

export type ProjectionMappingRecord = {
  id: string;
  tenant_id: string;
  integration_id: string;
  entity_type: string;
  entity_id: string;
  external_system: string;
  external_ref?: string | null;
  external_state?: Record<string, unknown> | null;
  projection_status: string;
  last_projected_at?: string | null;
  last_synced_at?: string | null;
  adapter_type?: string | null;
  adapter_capabilities: string[];
  sync_source?: string | null;
  conflicts: Array<Record<string, unknown>>;
  supported_resolution_actions: string[];
  resolution_guidance?: string | null;
};

export type ReconciliationLogRecord = {
  id: string;
  projection_id: string;
  action: string;
  detail?: string | null;
  resolved_by?: string | null;
  created_at?: string | null;
};

export type AgentSessionMessageRecord = {
  id: string;
  session_id: string;
  request_id: string;
  sender_type: string;
  sender_id: string;
  message_type: string;
  body: string;
  created_at: string;
};

export type GovernedRuntimeSummary = {
  runtime_family: string;
  runtime_subtype?: string | null;
  session_kind: string;
  adapter_type?: string | null;
  environment_ref?: string | null;
  thread_ref?: string | null;
  turn_ref?: string | null;
  pending_approval_count: number;
  pending_artifact_count: number;
  external_bindings: Array<Record<string, unknown>>;
};

export type AgentSessionRecord = {
  id: string;
  request_id: string;
  integration_id: string;
  integration_name: string;
  agent_label: string;
  collaboration_mode: string;
  agent_operating_profile: string;
  provider?: string | null;
  runtime_subtype?: string | null;
  session_kind: string;
  status: string;
  awaiting_human: boolean;
  summary: string;
  external_session_ref?: string | null;
  assigned_by: string;
  assigned_at: string;
  updated_at: string;
  governed_runtime?: GovernedRuntimeSummary | null;
  latest_message?: AgentSessionMessageRecord | null;
  message_count: number;
};

export type AgentSessionDetail = AgentSessionRecord & {
  messages: AgentSessionMessageRecord[];
};

export type ContextBundleRecord = {
  id: string;
  tenant_id: string;
  request_id: string;
  session_id?: string | null;
  version: number;
  bundle_type: string;
  contents: Record<string, unknown>;
  policy_scope?: Record<string, unknown> | null;
  assembled_by: string;
  assembled_at?: string | null;
  provenance: Array<Record<string, unknown>>;
};

export type ContextAccessLogRecord = {
  id: string;
  bundle_id: string;
  accessor_type: string;
  accessor_id: string;
  accessed_resource: string;
  access_result: string;
  policy_basis?: Record<string, unknown> | null;
  accessed_at?: string | null;
};

export type AgentSessionToolRecord = {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  required_collaboration_mode?: string | null;
  allowed_roles: string[];
  availability: string;
  availability_reason?: string | null;
};

export type AgentSessionContextDetail = {
  bundle: ContextBundleRecord;
  governed_runtime?: GovernedRuntimeSummary | null;
  available_tools: AgentSessionToolRecord[];
  restricted_tools: AgentSessionToolRecord[];
  degraded_tools: AgentSessionToolRecord[];
  capability_warnings: string[];
  access_log: ContextAccessLogRecord[];
};

export type ImportAgentSessionArtifactInput = {
  actor_id?: string;
  artifact_key: string;
  title: string;
  artifact_type?: string;
  summary?: string;
  content?: string | null;
  path?: string | null;
  source_ref?: string | null;
  image_ref?: string | null;
  promotion_relevant?: boolean;
  reason?: string;
};

export type CompleteAgentSessionInput = {
  actor_id?: string;
  reason?: string;
  target_status?: string | null;
  completion_action?: string;
};

export type ResumeAgentSessionRuntimeInput = {
  actor_id?: string;
  work_item_id: string;
  note?: string | null;
  target_status?: string | null;
  reason?: string;
};

export type ApproveAgentSessionCheckpointInput = {
  actor_id?: string;
  work_item_id: string;
  policy?: string;
  target_status?: string | null;
  reason?: string;
};

export type CreateIntegrationInput = {
  id: string;
  name: string;
  type: string;
  status?: string;
  endpoint: string;
  settings?: Record<string, unknown>;
};

export type UpdateIntegrationInput = {
  name: string;
  type: string;
  status?: string;
  endpoint: string;
  settings?: Record<string, unknown>;
  clear_api_key?: boolean;
  clear_access_token?: boolean;
};
