Application Build Specification Pack







Part 1: Canonical Domain Model





This is the authoritative object grammar for the application.

An implementation agent must not invent alternate core entities without explicit approval.





1. Global conventions







1.1 ID rules





All primary IDs are opaque strings.



Examples:



req_...
run_...
art_...
rev_...
cap_...






1.2 Audit fields





Every persisted entity must include:



id
created_at
created_by
updated_at
updated_by
tenant_id
version






1.3 Status fields





Statuses must be enums, never free text.





1.4 Soft delete





Core governed entities are never hard-deleted in normal operation. Use:



archived_at
archived_by
is_archived









2. Request







Purpose





Primary governed unit of work.





Schema



Request:
  id: string
  tenant_id: string
  request_type: string
  template_id: string
  template_version: string
  title: string
  summary: string
  status:
    enum:
      - draft
      - submitted
      - validation_failed
      - validated
      - classified
      - ownership_resolved
      - planned
      - queued
      - in_execution
      - awaiting_input
      - awaiting_review
      - under_review
      - changes_requested
      - approved
      - rejected
      - promotion_pending
      - promoted
      - completed
      - failed
      - canceled
      - archived
  priority:
    enum: [low, medium, high, urgent]
  sla_policy_id: string|null
  submitter_id: string
  owner_team_id: string|null
  owner_user_id: string|null
  workflow_binding_id: string|null
  current_run_id: string|null
  policy_context: object
  input_payload: object
  tags: string[]
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer
  is_archived: boolean


Rules





template_id and template_version are immutable after submission.
input_payload may only change by governed amendment event.
status changes only through allowed transitions.
Externally initiated onboarding and registration still materialize as Request records bound to immutable request templates. A separate unaudited registration store is not allowed for governed user onboarding.
Administrative navigation and APIs SHALL honor the tenant hierarchy explicitly. Platform-admin journeys SHALL expose tenants above organizations, while tenant-admin journeys SHALL be limited to the organizations, teams, users, and portfolios of the current tenant.









3. RequestTemplate







Purpose





Defines structure, governance, and default routing for a request class.





Schema



RequestTemplate:
  id: string
  tenant_id: string
  key: string
  version: string
  name: string
  description: string
  category: string
  status:
    enum: [draft, published, deprecated, archived]
  schema: object
  ui_schema: object
  default_priority:
    enum: [low, medium, high, urgent]
  workflow_family: string|null
  ownership_policy_id: string|null
  required_review_policy_id: string|null
  required_check_policy_id: string|null
  expected_artifact_types: string[]
  promotion_required: boolean
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version_number: integer


Specialization



At least one published template family SHALL support governed user-registration and account lifecycle changes. Those templates SHALL be usable from externally facing intake journeys and from internal administrative workflows.


Rules





Published templates are immutable.
New behavior requires new template version.
schema is canonical for validation.









4. WorkflowBinding







Purpose





Maps a request to an executable workflow.





Schema



WorkflowBinding:
  id: string
  tenant_id: string
  workflow_family: string
  workflow_identifier: string
  workflow_version: string
  runtime_target:
    enum: [foundry, agent_framework, external]
  dispatch_mode:
    enum: [static, dynamic, hybrid]
  expected_artifact_types: string[]
  retry_policy_id: string|null
  timeout_policy_id: string|null
  analytics_profile_id: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







5. Run







Purpose





Represents one execution instance for a request.





Schema



Run:
  id: string
  tenant_id: string
  request_id: string
  workflow_binding_id: string
  runtime_system:
    enum: [foundry, agent_framework, external]
  runtime_identifier: string|null
  status:
    enum:
      - pending_dispatch
      - dispatched
      - starting
      - running
      - waiting
      - completed
      - failed
      - canceled
      - timed_out
  governance_status:
    enum:
      - active
      - blocked
      - awaiting_input
      - terminal
  current_step_id: string|null
  started_at: datetime|null
  ended_at: datetime|null
  cost_amount: decimal|null
  cost_currency: string|null
  trace_ref: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







6. RunStep







Purpose





Fine-grained step record for workflow execution.





Schema



RunStep:
  id: string
  tenant_id: string
  run_id: string
  step_key: string
  step_type:
    enum: [agent, tool, human_task, check, approval, routing, wait, promotion]
  status:
    enum: [pending, running, waiting, completed, failed, skipped, canceled]
  started_at: datetime|null
  ended_at: datetime|null
  assigned_agent_id: string|null
  assigned_user_id: string|null
  input_ref: string|null
  output_ref: string|null
  error_summary: string|null
  trace_ref: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







7. Artifact







Purpose





Governed output or intermediate result.





Schema



Artifact:
  id: string
  tenant_id: string
  request_id: string
  run_id: string|null
  artifact_type:
    enum:
      - document
      - code_bundle
      - dataset
      - report
      - configuration
      - design
      - test_result
      - workflow_output
      - generated_media
      - structured_payload
      - validation_result
      - change_set
      - agent_definition
      - workflow_definition
      - tool_definition
      - runtime_binding_definition
      - policy_bundle
      - template_definition
  name: string
  current_version_id: string|null
  status:
    enum: [draft, under_review, approved, rejected, superseded, archived]
  produced_by_step_id: string|null
  promotion_relevant: boolean
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







8. ArtifactVersion







Purpose





Immutable version snapshot of an artifact.





Schema



ArtifactVersion:
  id: string
  tenant_id: string
  artifact_id: string
  version_label: string
  storage_uri: string
  mime_type: string
  checksum: string|null
  size_bytes: integer|null
  lineage_parent_version_id: string|null
  diff_base_version_id: string|null
  generated_by_run_id: string|null
  generated_by_step_id: string|null
  review_state:
    enum: [none, pending, commented, approved, changes_requested, blocked, stale]
  created_at: datetime
  created_by: string







9. Review







Purpose





Formal review attached to request, artifact, change set, or promotion.





Schema



Review:
  id: string
  tenant_id: string
  request_id: string
  scope_type:
    enum: [request, artifact, artifact_version, change_set, diff_region, promotion, capability]
  scope_id: string
  reviewer_id: string
  reviewer_role: string
  state:
    enum: [pending, commented, approved, changes_requested, blocked, stale, superseded]
  comment: string|null
  submitted_at: datetime|null
  stale_reason: string|null
  superseded_by_review_id: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







10. CheckResult







Purpose





Evaluation record for checks and policies.





Schema



CheckResult:
  id: string
  tenant_id: string
  request_id: string
  run_id: string|null
  scope_type:
    enum: [request, artifact, artifact_version, change_set, promotion, capability]
  scope_id: string
  check_key: string
  check_class:
    enum: [advisory, required, blocking]
  status:
    enum: [pending, passed, failed, skipped, overridden]
  evidence_ref: string|null
  evaluated_by:
    enum: [policy_engine, validator, agent, external_system, human]
  evaluated_at: datetime|null
  override_reason: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







11. ConversationThread







Purpose





Scoped interaction stream.





Schema



ConversationThread:
  id: string
  tenant_id: string
  request_id: string
  scope_type:
    enum: [request, run, artifact, promotion]
  scope_id: string
  title: string|null
  status:
    enum: [active, closed, archived]
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







12. Message







Purpose





Conversation entry.





Schema



Message:
  id: string
  tenant_id: string
  thread_id: string
  actor_type:
    enum: [user, agent, system]
  actor_id: string
  message_type:
    enum: [text, status, question, answer, command_ack, warning, error]
  body: string
  structured_payload: object|null
  created_at: datetime







13. Command







Purpose





Structured, auditable control action.





Schema



Command:
  id: string
  tenant_id: string
  request_id: string
  scope_type:
    enum: [run, request, promotion, capability]
  scope_id: string
  command_type:
    enum:
      - pause_run
      - resume_run
      - cancel_run
      - retry_step
      - add_context
      - answer_question
      - request_regeneration
      - escalate_review
      - request_replan
      - initiate_promotion
      - apply_override
      - rollback_capability
      - activate_capability
      - deactivate_capability
  payload: object
  status:
    enum: [pending, accepted, rejected, completed, failed]
  issued_by: string
  created_at: datetime
  processed_at: datetime|null







14. Workspace







Purpose





Isolated mutable work area, especially for repository-backed work.





Schema



Workspace:
  id: string
  tenant_id: string
  request_id: string
  repository_binding_id: string|null
  base_ref: string|null
  working_ref: string|null
  status:
    enum: [created, active, paused, invalid, closed, archived]
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







15. ChangeSet







Purpose





Governed unit of proposed modifications.





Schema



ChangeSet:
  id: string
  tenant_id: string
  request_id: string
  workspace_id: string
  status:
    enum:
      - opened
      - updated
      - validation_failed
      - under_review
      - approved
      - blocked
      - stale
      - superseded
      - promotion_ready
      - promoted
      - closed
  target_ref: string|null
  diff_summary: string|null
  changed_object_count: integer
  lineage_ref: string|null
  current_artifact_version_id: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







16. PromotionDecision







Purpose





Formal authorization and execution of final acceptance.





Schema



PromotionDecision:
  id: string
  tenant_id: string
  request_id: string
  scope_type:
    enum: [artifact, change_set, capability]
  scope_id: string
  target_type:
    enum: [repository_branch, publication_channel, runtime_registry, external_system]
  target_ref: string
  strategy: string
  status:
    enum: [pending, authorized, executing, completed, failed, canceled]
  approved_by: string|null
  executed_by: string|null
  executed_at: datetime|null
  result_ref: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







17. Capability







Purpose





Registry entry for executable platform capability.





Schema



Capability:
  id: string
  tenant_id: string
  capability_type:
    enum: [agent, workflow, tool, template, policy, runtime_binding]
  key: string
  name: string
  active_version_id: string|null
  status:
    enum: [draft, under_review, approved, published, active, deprecated, archived]
  owner_team_id: string|null
  created_at: datetime
  created_by: string
  updated_at: datetime
  updated_by: string
  version: integer







18. CapabilityVersion







Purpose





Versioned executable definition.





Schema



CapabilityVersion:
  id: string
  tenant_id: string
  capability_id: string
  version_label: string
  artifact_version_id: string
  compatibility_metadata: object
  activation_status:
    enum: [draft, approved, published, active, deprecated, archived]
  activated_at: datetime|null
  deprecated_at: datetime|null
  created_at: datetime
  created_by: string







19. MetricRecord







Purpose





Aggregated workflow intelligence record.





Schema



MetricRecord:
  id: string
  tenant_id: string
  metric_key: string
  scope_type:
    enum: [request, run, workflow, template, agent, reviewer, team, capability]
  scope_id: string
  period_start: datetime
  period_end: datetime
  value_numeric: decimal
  unit: string
  dimension_set: object
  source_lineage_ref: string
  calculated_at: datetime
  metric_definition_version: string







Part 2: Screen Contracts





These are the canonical frontend contracts.

An implementation agent must follow them exactly.





1. Global route structure



/requests
/requests/:requestId

/runs
/runs/:runId

/artifacts
/artifacts/:artifactId
/artifacts/:artifactId/versions/:versionId

/reviews
/reviews/queue

/promotions
/promotions/:promotionId

/capabilities
/capabilities/:capabilityId

/workspaces
/workspaces/:workspaceId

/analytics
/analytics/workflows
/analytics/agents
/analytics/bottlenecks
/analytics/cost

/admin/templates
/admin/policies
/admin/integrations







2. Request List







Route





/requests





Primary persona





Submitter, reviewer, operator





Purpose





Primary navigation surface for all work.





Data dependencies





paginated request list
filter metadata
saved views
user role context






Required table columns





ID
Type
Title
Status
Owner
Priority
Current Phase
Blocking Status
SLA Risk
Updated At






Filters





status
type
owner
priority
SLA risk
created by
updated date range






Primary actions





Create Request
Save View






Secondary actions





Export list
Bulk assign
Bulk cancel if authorized






Empty state





explain what requests are
primary CTA: Create Request






Loading state





skeleton table rows






Error state





persistent banner with retry









3. New Request







Route





/requests/new





Primary persona





Submitter





Purpose





Create request from template.





Required sections





template selector
dynamic form
validation summary
request summary sidebar






Primary actions





Save Draft
Submit Request






Secondary actions





Cancel






Rules





no hidden required fields
validation visible before submit
template version displayed before submit









4. Request Detail







Route





/requests/:requestId





Primary persona





All roles





Purpose





Canonical control plane for a request.





Required header





request ID
title
status
owner
blocking indicators
SLA risk
primary actions






Required tabs





Overview
Runs
Artifacts
Reviews
Conversations
History






Overview sections





request summary
current status
active blockers
latest run
latest artifacts
next required action






Primary actions





Cancel Request
Escalate
Re-run if permitted






Permissions behavior





Hide unauthorized actions, but do not hide state.








5. Runs List







Route





/runs





Primary persona





Operator





Purpose





Operational run management.





Required table columns





Run ID
Request ID
Workflow
Status
Current Step
Elapsed Time
Waiting Reason
Updated At






Filters





status
workflow
owner team
waiting
failed only
date range






Primary actions





Open Run






Secondary actions





Bulk retry if authorized
Bulk cancel if authorized









6. Run Detail







Route





/runs/:runId





Primary persona





Operator





Purpose





Execution monitoring and intervention.





Required layout





left: step timeline
center: current step detail
right: run context
bottom: conversation dock






Required sections





run summary
workflow identity
progress
current step input/output summary
wait condition or failure reason
command surface






Primary actions





Pause
Resume
Retry Step
Cancel Run






Rules





conversation dock is separate from execution detail
current step must always be visible without scrolling past unrelated content









7. Artifact List







Route





/artifacts





Primary persona





Reviewer, operator





Purpose





Browse all governed outputs.





Required table columns





Artifact ID
Type
Name
Current Version
Status
Request ID
Updated At
Owner






Filters





type
status
request ID
review state
promotion relevant
updated date range









8. Artifact Detail







Route





/artifacts/:artifactId





Primary persona





Reviewer





Purpose





Canonical review surface for an artifact.





Required layout





left: version list
center: content or diff
right: review panel






Required actions





Approve
Request Changes
Block
Comment






Rules





review actions must attach to selected version
chat cannot substitute for review
stale review must be visually obvious









9. Review Queue







Route





/reviews/queue





Primary persona





Reviewer





Purpose





Worklist for reviewable items.





Required table columns





Request
Review Scope
Artifact / Change Set
Type
Priority
SLA
Blocking Status
Assigned Reviewer






Filters





assigned to me
blocking only
stale only
type
due date
priority






Primary action





Open Review Item









10. Promotion Gate







Route





/promotions/:promotionId





Primary persona





Approver / operator





Purpose





Final governed acceptance screen.





Required sections





target
strategy
required checks
required approvals
stale warnings
execution readiness
promotion history






Primary actions





Dry Run
Authorize Promotion
Execute Promotion






Rules





no silent promotion
all unmet conditions shown inline









11. Capability Registry







Route





/capabilities





Primary persona





Admin, capability author





Purpose





Browse active and pending capabilities.





Required table columns





Name
Type
Version
Status
Owner
Updated At
Usage Count






Filters





type
status
owner
active only
deprecated only









12. Capability Detail







Route





/capabilities/:capabilityId





Primary persona





Admin, capability author





Purpose





Definition governance and lifecycle management.





Required tabs





Overview
Definition
Lineage
Usage
Performance
History






Required actions





Publish
Activate
Deprecate
Roll Back






Rules





active version must be explicit
system-defining artifacts must show elevated review requirements









13. Analytics - Workflow Performance







Route





/analytics/workflows





Primary persona





Executive, operator, manager





Purpose





Measure and optimize workflow performance.





Required table columns





Workflow
Avg Cycle Time
P95 Duration
Failure Rate
Review Delay
Cost per Execution
Trend






Filters





time window
workflow family
team
request type
SLA breach only






Required drill-down





metric row → underlying requests → request detail → run detail





Rules





analytics starts with tables, not charts
any chart shown must support direct drill-down









14. Analytics - Agents







Route





/analytics/agents





Required table columns





Agent
Invocations
Success Rate
Retry Rate
Avg Duration
Cost per Invocation
Quality Score









15. Analytics - Bottlenecks







Route





/analytics/bottlenecks





Required table columns





Workflow
Step
Avg Wait Time
Block Count
Reviewer Delay
Trend









16. Audit / History







Route





/requests/:requestId/history





Primary persona





Auditor, operator, admin





Purpose





Authoritative trace of governed changes.





Required table columns





Timestamp
Actor
Action
Object Type
Object ID
Reason / Evidence






Rules





immutable ordering
export supported
no hidden fields in audit view









17. Admin - Templates







Route





/admin/templates





Primary persona





Admin





Purpose





Manage request templates.





Required layout





left: template/version list
center: definition editor/viewer
right: publish/validation panel






Primary actions





Create Version
Create Template
Validate
Publish
Deprecate
Delete Draft
Save Draft
Preview Definition
Compare Versions









18. Admin - Policies







Route





/admin/policies





Purpose





Manage policy bundles and check rules.








19. Admin - Integrations







Route





/admin/integrations





Purpose





Manage Foundry, Agent Framework, GitHub/MCP, IdP, and notification integrations.

Agent-capable integrations SHALL support direct request assignment and persistent interactive agent sessions, with request drill-down links into the active session transcript.
