# End-to-End User Stories

This file defines the end-to-end user stories used to validate the platform against the constitution, requirements, and build pack.

The executable coverage for these stories lives in:

- `/Volumes/data/development/rgp/tests/integration/test_end_to_end_user_stories.py`

## US-01 Template Authoring Lifecycle

An administrator creates a new draft template, authors its schema and routing, validates it, publishes it, creates a successor draft version, and removes that unused draft.

Covers:

- template draft creation
- template definition editing
- template validation
- previewable definition shape
- publishing immutable versions
- successor draft versions
- controlled draft deletion

Primary requirement areas:

- request templates and immutable versioning
- template authoring surface
- template validation, preview, publication, comparison, and draft removal

## US-02 Organization And Integration Administration

An administrator creates and updates users, teams, memberships, portfolios, and integrations, then verifies those records appear in the platform catalogs.

Covers:

- user creation and update
- team creation and update
- multi-team membership management
- portfolio creation
- integration creation, update, and deletion
- provider settings persistence

Primary requirement areas:

- users, teams, portfolios
- tenant-scoped administration
- direct-assignment-capable integrations

## US-03 Request Mutation Controls

A submitter creates and submits a request, amends it, clones it, cancels the clone, supersedes the original with the clone lineage, and verifies the resulting request history and lineage records.

Covers:

- draft creation
- submission
- amendment
- cloning
- cancellation
- supersession
- request timeline and lineage

Primary requirement areas:

- draft save and submit
- governed mutation events
- cancellation, cloning, resubmission, and supersession
- full request timeline

## US-04 Agent-Assisted Governed Request

A submitter creates a governed request, assigns it to a real agent-capable integration, interacts with the agent across multiple turns, verifies real persisted outputs, accepts the result, and resumes the request workflow.

Covers:

- request-scoped interactive agent assignment
- persistent session transcript
- multi-turn human-agent collaboration
- real provider output persistence
- explicit session completion and workflow resume

Primary requirement areas:

- direct request-to-agent assignment
- persistent interactive sessions
- request-scoped conversations
- agent outputs and execution metadata

## US-05 Review, Promotion, And Completion

An operator/reviewer advances a request through validation, planning, execution, review, promotion authorization, deployment, and final completion.

Covers:

- request transitions
- automatic check gating
- review queue decisioning
- promotion preflight
- approval authorization
- deployment execution
- final completion

Primary requirement areas:

- unified request lifecycle
- review and approval gates
- promotion authorization and execution
- no completion or promotion without governance

## US-06 Events, Analytics, And Observability

An operator inspects the platform’s event ledger, outbox, organizational catalogs, delivery analytics, workflow analytics, agent analytics, performance analytics, and portfolio summaries after governed work has occurred.

Covers:

- unified event ledger
- outbox visibility
- workflow, agent, delivery, and performance analytics
- operational summaries and trends
- org and portfolio rollups

Primary requirement areas:

- event traceability
- workflow intelligence
- agent analytics
- performance and SLO visibility
- portfolio/team/user reporting

## US-07 Performance And Scalability Validation

An operator runs a governed performance suite that applies concurrent read and write workload against the live platform, validates latency/error/throughput thresholds, and confirms that the platform's own performance analytics surfaces reflect that workload.

Covers:

- concurrent read-path performance
- concurrent write-path performance
- threshold-based latency and error-rate validation
- throughput validation
- performance analytics capture of exercised routes

Primary requirement areas:

- runtime telemetry
- measurable performance reporting
- SLO-oriented operational validation
- evidence-backed scalability testing

## Execution Notes

- The current automated suite targets the live local API on `http://127.0.0.1:8001`.
- Development auth must remain enabled so the suite can issue a dev bearer token.
- The suite is integration-focused rather than browser-focused because the browser harness is not reliable enough in this environment for deterministic E2E validation.
