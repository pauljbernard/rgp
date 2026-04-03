Request Governance Platform







Execution Specification Pack







Version 1.0










1. Implementation Lock





These choices are fixed unless explicitly changed.





1.1 Frontend





Framework: Next.js with React and TypeScript
Styling: Tailwind CSS
State/query: TanStack Query
Tables: TanStack Table
Forms: React Hook Form + Zod
Routing: Next.js App Router
Charts: minimal, Recharts only where explicitly required






1.2 Backend





Framework: FastAPI with Python
Validation: Pydantic
Auth: OIDC/SAML via gateway + JWT claims propagation
Async tasks: Celery or equivalent worker layer
Event publishing: Kafka-compatible bus
Streaming: Server-Sent Events for UI updates






1.3 Data





Operational DB: PostgreSQL
Event Store: append-only events table in PostgreSQL for MVP, abstracted behind repository
Artifact Store: object storage
Metrics Warehouse: PostgreSQL analytical schema for MVP, separable later
Cache: Redis






1.4 Infra





Containerized services
Reverse proxy / ingress
OpenTelemetry everywhere
Secrets in managed secret store









2. Repository Structure Contract



rgp/
  apps/
    web/
    api/
    worker/
  packages/
    ui/
    domain/
    api-client/
    config/
    telemetry/
  docs/
    constitution/
    requirements/
    ux/
    api/
    events/
  infra/
    docker/
    k8s/
    terraform/
  scripts/
  tests/
    unit/
    integration/
    e2e/
    fixtures/
Rules:



apps/web contains only frontend app code
apps/api contains HTTP API and orchestration entrypoints
apps/worker contains async job consumers
packages/domain contains shared enums, schema contracts, and business rules
generated API client goes in packages/api-client









3. API Contract Standard







3.1 General Rules





All APIs are versioned under /api/v1
JSON only
ISO-8601 timestamps
server-side pagination everywhere for lists
filtering and sorting standardized
all mutations are auditable






3.2 Pagination Format





Request query params:



page
page_size
sort
filter




Response shape:

{
  "items": [],
  "page": 1,
  "page_size": 25,
  "total_count": 132,
  "total_pages": 6
}


3.3 Sort Syntax



sort=updated_at:desc,status:asc


3.4 Filter Syntax





Use repeated query params:

?status=in_execution&status=awaiting_review&owner_team_id=team_ops
For complex filtering, POST search endpoints are allowed:

{
  "filters": [
    {"field": "status", "op": "in", "value": ["awaiting_review", "under_review"]},
    {"field": "priority", "op": "eq", "value": "high"}
  ],
  "sort": [{"field": "updated_at", "dir": "desc"}],
  "page": 1,
  "page_size": 50
}


3.5 Error Envelope





All non-2xx responses:

{
  "error": {
    "code": "REQUEST_VALIDATION_FAILED",
    "message": "Request payload failed validation.",
    "details": [
      {"field": "input_payload.subject", "message": "Field is required"}
    ],
    "correlation_id": "corr_123",
    "retryable": false
  }
}


3.6 Idempotency





All mutation endpoints that can be retried must accept:



Idempotency-Key header




Behavior:



same key + same payload = same result
same key + different payload = 409









4. Core API Surface





This is the minimum canonical API.





4.1 Requests







Create draft





POST /api/v1/requests

{
  "template_id": "tmpl_curriculum",
  "template_version": "3.1.0",
  "title": "Generate Grade 5 Math Unit",
  "summary": "Create initial unit scope",
  "priority": "high",
  "input_payload": {}
}


Submit request





POST /api/v1/requests/{request_id}/submit





Amend request





POST /api/v1/requests/{request_id}/amend

{
  "reason": "Added standards reference",
  "patch": {
    "input_payload": {
      "standards": ["TEKS-5.3A"]
    }
  }
}


List requests





GET /api/v1/requests





Get request





GET /api/v1/requests/{request_id}





Search requests





POST /api/v1/requests/search





Cancel request





POST /api/v1/requests/{request_id}/cancel





Clone request





POST /api/v1/requests/{request_id}/clone








4.2 Templates







List templates





GET /api/v1/templates





Get template





GET /api/v1/templates/{template_id}/versions/{version}





Validate payload





POST /api/v1/templates/{template_id}/versions/{version}/validate





Create template version





POST /api/v1/templates/{template_id}/versions





Publish template version





POST /api/v1/templates/{template_id}/versions/{version}/publish








4.3 Runs







List runs





GET /api/v1/runs





Get run





GET /api/v1/runs/{run_id}





Pause run





POST /api/v1/runs/{run_id}/pause





Resume run





POST /api/v1/runs/{run_id}/resume





Cancel run





POST /api/v1/runs/{run_id}/cancel





Retry step





POST /api/v1/runs/{run_id}/steps/{step_id}/retry





Inject context





POST /api/v1/runs/{run_id}/context








4.4 Artifacts







List artifacts





GET /api/v1/artifacts





Get artifact





GET /api/v1/artifacts/{artifact_id}





Get artifact version





GET /api/v1/artifacts/{artifact_id}/versions/{version_id}





Register artifact version





POST /api/v1/artifacts/{artifact_id}/versions





Diff versions





GET /api/v1/artifacts/{artifact_id}/diff?left={v1}&right={v2}








4.5 Reviews







List review queue





GET /api/v1/reviews/queue





Submit review





POST /api/v1/reviews

{
  "request_id": "req_123",
  "scope_type": "artifact_version",
  "scope_id": "artv_456",
  "state": "approved",
  "comment": "Looks correct"
}


Mark stale





POST /api/v1/reviews/{review_id}/mark-stale








4.6 Promotions







Create promotion request





POST /api/v1/promotions





Get promotion





GET /api/v1/promotions/{promotion_id}





Dry run





POST /api/v1/promotions/{promotion_id}/dry-run





Authorize





POST /api/v1/promotions/{promotion_id}/authorize





Execute





POST /api/v1/promotions/{promotion_id}/execute








4.7 Conversations and Commands







List threads





GET /api/v1/threads?request_id=req_123





Post message





POST /api/v1/threads/{thread_id}/messages





Post command





POST /api/v1/commands





Stream updates





GET /api/v1/streams/requests/{request_id}








4.8 Capabilities







List capabilities





GET /api/v1/capabilities





Get capability





GET /api/v1/capabilities/{capability_id}





Create capability version





POST /api/v1/capabilities/{capability_id}/versions





Publish capability version





POST /api/v1/capabilities/{capability_id}/versions/{version_id}/publish





Activate capability version





POST /api/v1/capabilities/{capability_id}/versions/{version_id}/activate





Roll back





POST /api/v1/capabilities/{capability_id}/rollback








4.9 Analytics







Workflow metrics





GET /api/v1/analytics/workflows





Agent metrics





GET /api/v1/analytics/agents





Bottlenecks





GET /api/v1/analytics/bottlenecks





Cost analytics





GET /api/v1/analytics/cost








5. Event Model







5.1 Event Envelope





Every event uses:

{
  "event_id": "evt_123",
  "event_type": "RequestSubmitted",
  "event_version": "1.0",
  "tenant_id": "tenant_1",
  "request_id": "req_123",
  "scope_type": "request",
  "scope_id": "req_123",
  "occurred_at": "2026-03-30T12:00:00Z",
  "actor_type": "user",
  "actor_id": "usr_42",
  "correlation_id": "corr_abc",
  "causation_id": "cmd_789",
  "payload": {}
}


5.2 Canonical Event Types







Request lifecycle





RequestCreated
RequestDraftSaved
RequestSubmitted
RequestValidationFailed
RequestValidated
RequestClassified
OwnershipResolved
WorkflowBound
RequestAmended
RequestCanceled
RequestCompleted
RequestRejected
RequestFailed






Run lifecycle





RunDispatched
RunStarted
StepStarted
StepCompleted
StepFailed
RunWaiting
RunResumed
RunCanceled
RunCompleted
RunFailed






Artifact lifecycle





ArtifactRegistered
ArtifactVersionCreated
ArtifactSuperseded






Review lifecycle





ReviewRequested
ReviewSubmitted
ReviewMarkedStale
ApprovalGranted
ChangesRequested
ReviewBlocked






Check lifecycle





CheckEvaluated
CheckOverridden






Promotion lifecycle





PromotionRequested
PromotionDryRunCompleted
PromotionAuthorized
PromotionExecuted
PromotionCompleted
PromotionFailed






Capability lifecycle





CapabilityVersionCreated
CapabilityApproved
CapabilityPublished
CapabilityActivated
CapabilityDeprecated
CapabilityRolledBack






Conversation / command





MessagePosted
CommandIssued
CommandAccepted
CommandRejected
CommandCompleted
CommandFailed






5.3 Ordering Rules





ordering is guaranteed per request stream
global ordering is not guaranteed
replay is per request or per aggregate root






5.4 Idempotency Rules





every event has unique event_id
command-caused events must preserve causation_id
replay must not re-run side effects unless explicitly marked replay-safe









6. State Transition Matrix







6.1 Request Transitions



From

To

Trigger

Allowed

draft

submitted

submit

yes

submitted

validation_failed

validate fail

yes

submitted

validated

validate pass

yes

validated

classified

classification complete

yes

classified

ownership_resolved

ownership resolved

yes

ownership_resolved

planned

workflow binding complete

yes

planned

queued

dispatch scheduled

yes

queued

in_execution

run started

yes

in_execution

awaiting_input

run waiting

yes

in_execution

awaiting_review

terminal artifact ready

yes

awaiting_input

in_execution

input provided

yes

awaiting_review

under_review

review opened

yes

under_review

changes_requested

review result

yes

under_review

approved

all approvals satisfied

yes

approved

promotion_pending

promotion required

yes

approved

completed

no promotion required

yes

promotion_pending

promoted

promotion complete

yes

promoted

completed

finalize

yes

any non-terminal

failed

unrecoverable failure

yes

any non-terminal

canceled

cancel action

yes

Disallowed:



completed → any non-terminal
rejected → in_execution
archived → anything else






6.2 Review Staleness





A review becomes stale when:



reviewed artifact version changes
associated change set changes materially
promotion target changes materially
policy for request class requires re-review after rerun






6.3 Capability Transitions



From

To

Trigger

draft

under_review

review requested

under_review

approved

approvals satisfied

approved

published

publish action

published

active

activate action

active

deprecated

deprecate action

active

active

rollback to prior active version

deprecated

archived

archive action








7. Permission Matrix







7.1 Roles





submitter
reviewer
approver
operator
admin
capability_author
executive
service_identity
agent_identity






7.2 Action Matrix



Action

Submitter

Reviewer

Approver

Operator

Admin

Capability Author

create request

Y

N

N

N

Y

Y

amend own request

Y

N

N

N

Y

Y

cancel request

limited

N

N

limited

Y

limited

view request

Y

Y

Y

Y

Y

Y

submit review

N

Y

Y

N

Y

Y

approve

N

limited

Y

N

Y

limited

pause run

N

N

N

Y

Y

N

retry step

N

N

N

Y

Y

N

execute promotion

N

N

Y

limited

Y

limited

publish capability

N

N

N

N

Y

Y

activate capability

N

N

N

N

Y

limited

override failed check

N

N

limited

limited

Y

N

mutate repository via MCP

N

N

N

limited

Y

limited

“limited” means policy-dependent.








8. Concurrency Model







8.1 Optimistic Concurrency





All mutable entities use version-based optimistic concurrency.

Client must send current version on mutation.

Version mismatch returns 409 CONFLICT.





8.2 Review Conflicts





If two reviewers act simultaneously:



both reviews persist
approval aggregation recalculates
if one is stale at calculation time, it does not count






8.3 Promotion Conflicts





Only one active promotion execution per scope object.

Second execution attempt returns 409 PROMOTION_IN_PROGRESS.





8.4 Run Command Conflicts





Commands on terminal runs are rejected with 409 INVALID_RUN_STATE.








9. Physical Data Strategy







9.1 PostgreSQL Tables





requests
request_templates
workflow_bindings
runs
run_steps
artifacts
artifact_versions
reviews
check_results
conversation_threads
messages
commands
workspaces
change_sets
promotion_decisions
capabilities
capability_versions
metric_records
events






9.2 Indexing





Minimum indexes:



requests: (tenant_id, status, updated_at desc)
runs: (tenant_id, request_id, started_at desc)
artifacts: (tenant_id, request_id, artifact_type)
reviews: (tenant_id, scope_type, scope_id, state)
events: (tenant_id, request_id, occurred_at asc)
metric_records: (tenant_id, metric_key, scope_type, period_start desc)






9.3 Tenant Partitioning





Every table includes tenant_id.

All queries must be tenant-scoped.

No cross-tenant query path allowed in application layer.








10. Error Model







10.1 Error Codes





Canonical codes:



REQUEST_VALIDATION_FAILED
INVALID_STATE_TRANSITION
PERMISSION_DENIED
RESOURCE_NOT_FOUND
CONFLICT
EXTERNAL_RUNTIME_FAILURE
POLICY_CHECK_FAILED
PROMOTION_BLOCKED
STALE_REVIEW
INTEGRATION_UNAVAILABLE
RATE_LIMITED
INTERNAL_ERROR






10.2 Retryability





Errors must explicitly indicate retryable: true|false.





10.3 User-Safe Messages





User-visible message must be clear and non-leaky.

Internal diagnostics go to logs and traces.








11. Integration Adapter Contracts







11.1 Foundry Adapter Contract





Input:

{
  "request_id": "req_123",
  "run_id": "run_123",
  "workflow_identifier": "wf_curriculum_v2",
  "input_payload": {},
  "context_refs": [],
  "policy_context": {}
}
Output:

{
  "runtime_identifier": "foundry_run_999",
  "accepted": true
}
Signal callbacks normalized to:



step started
step completed
artifact output
waiting
failed
completed






11.2 Agent Framework Adapter





Must support:



workflow dispatch
step lifecycle events
trace reference propagation
artifact emission callbacks






11.3 GitHub / MCP Adapter





Must support:



repo read
branch/workspace creation
patch/apply mutation
diff extraction
optional PR mirroring




Hard rules:



all mutating calls require request context
all mutating calls require actor attribution
protected targets cannot be written directly









12. Acceptance Test Harness







12.1 Golden Scenarios







Scenario A: Standard request lifecycle





Create request from template
Submit
Validate
Bind workflow
Dispatch run
Generate artifact
Review artifact
Approve
Complete






Scenario B: Stale review





Artifact reviewed and approved
New artifact version created
Review marked stale
Promotion blocked until re-review






Scenario C: Promotion flow





Request approved
Promotion requested
Dry run passes
Promotion authorized
Promotion executed
Request completed






Scenario D: Capability creation





Request generates workflow definition artifact
Definition reviewed
Capability published
Capability activated
Future request executes new capability






Scenario E: Operator intervention





Run fails at step
Operator opens run
Retry step command issued
Run resumes
Request continues






12.2 Test Levels





unit tests for domain services
contract tests for APIs
integration tests for adapters
replay tests for event model
e2e tests for core workflows
accessibility smoke tests









13. Seed Data Pack





Minimum fixtures:



3 request templates
10 requests across statuses
5 runs with mixed outcomes
12 artifacts with versions
8 reviews including stale and blocked
3 promotion decisions
4 capabilities with versions
100 metric records









14. Build Order







Phase 1





domain model
request APIs
template system
event store
request list/detail UI






Phase 2





runs
artifacts
reviews
promotion gate






Phase 3





Foundry + Agent Framework adapters
conversations and commands
workspaces and change sets






Phase 4





capability registry
homoiconic flows
analytics






Phase 5





enterprise hardening
billing
advanced operational tooling









15. Final Readiness Assessment





With the constitution, requirements, design system, screen contracts, component contracts, decision tables, integration contracts, and this execution specification pack, the remaining ambiguity for a coding agent is now reasonably low.



What is now sufficiently constrained:



core architecture
domain entities
API patterns
event patterns
state transitions
permissions
UX structure
component inventory
integration seams
test scenarios
build sequence
