# RGP Lambda + DynamoDB Remediation Plan

This backlog translates the platform-standard remediation into concrete RGP work.

## Current Status

Completed:
- Constitution amended to declare Lambda-compatible runtime and DynamoDB as the canonical target for core RGP services.
- Initial persistence ports added for templates and requests.
- Persistence inventory documented in `lambda_dynamodb_inventory.md`.
- DynamoDB config and first-slice adapter scaffold added for request/template migration.
- Template slice now has a functional DynamoDB adapter, explicit backend selector, and seed helper.
- Request slice now has a functional DynamoDB adapter for core lifecycle mutations and basic lifecycle reads.
- Request mutation parity is now verified against DynamoDB Local via `scripts/verify-request-dynamodb-parity.py`.
- Request lifecycle backend selection is now dynamic in `governance_service`.
- Request bootstrap/seed wiring now exists for DynamoDB local startup.
- Transitional request-state bridging now allows Dynamo-backed requests to participate in:
  - routing recommendation
  - SLA evaluation
  - request detail hydration for seeded/demo related views
  - request agent integration listing
  - assignment preview bundle assembly
- Additional write-side bridging now allows Dynamo-backed requests to participate in:
  - direct agent session assignment
  - agent session governance updates
  - escalation execution
- Request audit history now falls back to canonical DynamoDB events when no SQL `RequestTable` row exists.
- Agent-session async completion now uses conditional compare-and-set updates so background turns cannot overwrite a completed session back to `waiting_on_human`.
- Request check-run reads are now routed through the request lifecycle store, and the monolith falls back to DynamoDB-backed request check runs when the request slice is canonical there.
- Review queue and promotion read paths now resolve tenant-scoped request access through canonical request state when the request row is absent from SQL.
- Review mutations now work for Dynamo-backed requests, including reviewer reassignment and approval/changes-requested decisions.
- Promotion mutations now work for the bridged access/update surface on Dynamo-backed requests, including dry run, authorize, approval reassignment, and promotion-check queueing.
- Check-run ID generation was hardened to tolerate mixed legacy/non-numeric `cr_*` ids.
- Async check execution now resolves canonical request state for Dynamo-backed requests, so queued promotion checks can complete without a SQL `RequestTable` row.
- Analytics/reporting request loaders now merge canonical request records from SQL and DynamoDB, so tenant summaries no longer ignore Dynamo-backed requests.
- Transitional SQL-backed adapters added for:
  - request lifecycle
  - promotions and review queue
  - organization and tenant management
  - analytics queries
  - event queries
  - governance runtime operations
- Service boundaries refactored to depend on ports/adapters instead of repository singletons for:
  - `request_service`
  - `template_service`
  - `governance_service`

Inventory snapshot:
- direct `SessionLocal()` usages remaining across `app/services` and `app/repositories`: `223`
- direct repository imports remaining in `app/services`: `0`

## Phase 1: Constitutional And Boundary Corrections

1. Amend the constitution to declare Lambda-compatible runtime and DynamoDB as the canonical target for core RGP services.
   Files:
   - `constitution.md`
   Status:
   - completed

2. Introduce persistence ports so new service code stops depending directly on SQLAlchemy-backed repositories.
   Files:
   - `apps/api/app/persistence/contracts.py`
   - `apps/api/app/persistence/sql_governance_adapter.py`
   - `apps/api/app/services/request_service.py`
   - `apps/api/app/services/template_service.py`
   - `apps/api/app/persistence/sql_service_adapters.py`
   - `apps/api/app/services/governance_service.py`
   Status:
   - in progress
   - completed for the first public API service slices listed above
   - remaining services still need port-based isolation

## Phase 2: Inventory And Classification

3. Inventory all direct `SessionLocal()` usage and classify each call site by aggregate, read/write pattern, and transactional dependency.
   Primary files:
   - `apps/api/app/repositories/governance_repository.py`
   - `apps/api/app/services/*`
   Status:
   - inventory started
   - coarse count captured in the snapshot above
   - aggregate-by-aggregate classification still pending

4. Produce an access-pattern matrix for the first migration slices:
   - templates
   - requests
   - reviews
   - promotions/check-runs
   Status:
   - pending

## Phase 3: DynamoDB Data Model

5. Define canonical item shapes, partition/sort keys, GSIs, and projection strategy for:
   - template versions
   - requests
   - request events
   - review decisions
   - promotion records

6. Define object-storage boundaries for large artifacts and bundle payloads.

## Phase 4: Vertical Slice Migration

7. Implement DynamoDB adapters for template persistence and request persistence behind the new ports.
   Status:
   - template slice partially implemented
   - request slice implemented for core lifecycle mutations
   - request slice now supports request-side reads for list/detail/history/check runs/relationships
   - transitional read bridging added for runs, artifacts, routing, SLA, and assignment preview
   - direct agent session assignment, follow-up messaging, completion, and escalation execution now bridge request-state writes into the canonical store
   - request audit history now works for Dynamo-only requests
   - request check-run reads now work for Dynamo-only requests through `governance_service.list_request_check_runs`
   - review queue reads and promotion detail/check-run reads now work for Dynamo-only requests
   - review mutation paths now bridge canonical request updates for Dynamo-only requests
   - promotion mutation paths now bridge tenant-scoped access for Dynamo-only requests through dry-run, authorize, approval reassignment, and check queueing
   - promotion check execution now completes for Dynamo-only requests via the local dispatcher and canonical request-state lookup
   - portfolio summaries, delivery summaries, workflow analytics, agent analytics, bottleneck analytics, and operations summaries now read canonical request records instead of only `RequestTable`
   - workflow audit timelines now resolve workflow request membership from canonical request records instead of only `RequestTable`
   - run list/detail and runtime callback reconciliation now resolve tenant access and request status updates from canonical request state when the request is Dynamo-backed
   - run audit timelines now resolve request access from canonical request state when the run points at a Dynamo-backed request
   - mixed-mode check enqueueing no longer falls back to a hardcoded `tenant_demo`; dispatcher tenant resolution now requires canonical request ownership
   - repository-level request-check queueing now resolves canonical request state instead of requiring a SQL `RequestTable` row
   - repository-level request mutations (`submit`, `amend`, `cancel`, `transition`, `clone`, `supersede`) now delegate to the DynamoDB adapter when the request is canonical-only
   - repository-level request list/detail reads now resolve canonical request state instead of only `RequestTable`
   - Dynamo-backed request events now dual-write into the SQL event store/outbox path so existing event consumers still observe canonical request mutations
   - Dynamo-backed request check enqueueing now dual-writes `check_run.enqueued` into the SQL event store/outbox path
   - Dynamo-backed request check runs now create SQL `CheckRunTable` rows for execution and sync status transitions back into the canonical Dynamo check-run items
   - Dynamo-backed request transitions now enforce request-gate preflight using the same transition-gate policy data as the SQL path
   - Dynamo-backed request transitions now invoke the shared side-effect helpers, enabling canonical transitions to create downstream run/review/promotion artifacts on non-runtime paths
   - local runtime/deployment mock endpoint resolution now rewrites the legacy `localhost:8001` seed to the internal self URL, so runtime-dispatch-dependent paths no longer break inside the container
   - artifact-event recording now resolves canonical request ownership instead of requiring a SQL `RequestTable` row
   - Dynamo-backed request check-run creation now reuses existing queued/running canonical runs instead of blindly creating duplicates
   - canonical request check-run completion/failure is now written back to DynamoDB after the SQL transaction commits, keeping transition gating ordered across both stores
   - planning construct progress and roadmap projections now resolve member request state through the canonical request bridge instead of only `RequestTable`
   - roadmap status buckets now count real lifecycle states like `queued`, `in_execution`, and `promotion_pending` as active work instead of underreporting them
   - relationship/dependency graph checks now resolve source request status through canonical request state instead of requiring SQL-backed request rows
   - view projections now resolve board/graph request nodes through canonical request state instead of only `RequestTable`
   - board projection now scans the full canonical request set for a tenant, so Dynamo-only requests are no longer omitted from status lanes
   - roadmap projection completion counts now resolve planning-member request state through canonical request lookup instead of only SQL request rows
   - projection conflict detection and external sync now resolve request canonical snapshots through the request bridge, so admin projection surfaces reflect Dynamo-only request status/title correctly
   - policy-engine transition evaluation now accepts canonical request records instead of requiring a SQL `RequestTable` object
   - queue-routing escalation execution now updates canonical request state through the request bridge instead of first requiring a SQL `RequestTable` row
   - longer-lived async agent execution paths still need broader end-to-end validation

8. Add dual-write / parity verification tooling for templates and requests.
   Status:
   - template parity script added in `scripts/verify-template-dynamodb-parity.py`
   - template parity verified successfully against DynamoDB Local
   - request parity script added in `scripts/verify-request-dynamodb-parity.py`
   - request mutation parity verified successfully against DynamoDB Local
   - live Dynamo-only request validation now covers agent assignment, follow-up message posting, completion, persisted session terminal state, and request audit history
   - live Dynamo-only request validation now also covers request check-run queue/read behavior through the governance service path used by the SSE events endpoint
   - live Dynamo-only request validation now covers review queue reads, review reassignment, review approval, promotion detail reads, promotion check-run reads, promotion approval reassignment, and promotion check queueing
   - live Dynamo-only request validation now covers promotion check execution to completion, including populated `required_checks` and updated readiness
   - live Dynamo-only request validation now covers analytics visibility in performance operations and portfolio/delivery summaries
   - live Dynamo-only request validation now covers workflow audit timelines
   - live Dynamo-only request validation now covers run list/detail and runtime callback reconciliation, including a canonical request transition from `queued` to `in_execution`
   - live Dynamo-only request validation now covers run audit timelines, including runtime callback history plus run status snapshot entries
   - live mixed-mode validation now covers direct `check_dispatch_service.enqueue_request_checks(...)` against a Dynamo-backed request, with successful queued check-run creation and no hardcoded tenant fallback
   - live Dynamo-only request validation now covers direct `governance_repository.run_request_checks(...)`, with successful queued request-check creation and canonical request return value
   - live Dynamo-only request validation now covers direct repository-level `amend`, `submit`, `clone`, `supersede`, and `cancel` mutation calls through `governance_repository`
   - live Dynamo-only request validation now covers direct repository-level request listing and detail reads through `governance_repository`
   - live Dynamo-only request validation now covers SQL event ledger and outbox visibility for direct Dynamo-backed request mutations
   - live Dynamo-only request validation now covers SQL event ledger and outbox visibility for both manual and submit-triggered request check enqueueing
   - live Dynamo-only request validation now covers canonical request check runs progressing from `queued` to `completed` after local execution
   - live Dynamo-only request validation now covers gated `submitted -> validated` transitions, including pending-check rejection and successful retry after checks complete
   - live Dynamo-only request validation now covers `in_execution -> awaiting_review` side effects, including artifact creation, review queue creation, and request check queueing
   - live Dynamo-only request validation now covers `approved -> promotion_pending` after review approval and check completion, including promotion-record creation and promotion-check queueing
   - live Dynamo-only request validation now covers workflow audit timelines, with workflow membership resolved from canonical request records instead of only `RequestTable`
   - live Dynamo-only request validation now covers repository-level `command_run(...)` against a run whose request exists only in DynamoDB, with accepted runtime dispatch recorded in `runtime_dispatches`
   - live Dynamo-only request validation now covers `planned -> queued` runtime enqueue dispatch, including a single completed canonical request check run and an accepted runtime enqueue response for the generated run
   - live planning validation now covers a planning construct whose sole membership is a Dynamo-only request, with `aggregate_progress(...)` reporting that member and the roadmap view counting it as `in_progress`
   - live dependency validation now covers a Dynamo-only source request blocking a Dynamo-only target through a `depends_on` edge, with blocker detection clearing after source cancellation
   - live view-projection validation now covers board lanes containing Dynamo-only queued requests and graph projection of a Dynamo-only dependency edge
   - live projection validation now covers creating, syncing, and conflict-detecting a repository projection for a Dynamo-only request
   - live policy-engine validation now covers transition evaluation for a Dynamo-only request, including legacy transition-gate actions for `promotion_pending`
   - live queue-routing validation now covers recommendation plus escalation execution for a Dynamo-only request, including canonical owner-team update and audit history
   - workspace creation now resolves canonical request ownership before persisting, so caller-supplied tenant mismatches are rejected for Dynamo-backed requests
   - workflow execution startup now resolves canonical request ownership before persisting, and the workflow engine's event-store writes now use the active SQL session correctly
   - live validation now covers workspace creation, workflow startup, and tenant-mismatch rejection for a Dynamo-only request
   - change set creation and lifecycle transitions now resolve canonical request ownership before persisting, and tenant-scoped reads reject mismatched tenants for Dynamo-backed requests
   - live validation now covers change set create/read/submit/apply plus tenant-mismatch rejection for a Dynamo-only request
   - editorial workflow creation and stage/assignment mutations now resolve canonical request ownership before persisting, and tenant-scoped reads reject mismatched tenants for Dynamo-backed requests
   - live validation now covers editorial workflow create/read/advance/assign plus tenant-mismatch rejection for a Dynamo-only request
   - content projection creation and reads now derive tenant ownership from the artifact's canonical request ownership instead of trusting caller-supplied tenant context
   - live validation now covers content projection create/list/read plus tenant-mismatch rejection for a tenant-demo artifact owned by a canonical request
   - knowledge reuse tracking now validates that the target request belongs to the same tenant as the knowledge artifact before provenance is updated
   - live validation now covers knowledge artifact creation, same-tenant reuse provenance update, and cross-tenant reuse rejection using a canonical tenant-other request item
   - context bundle retrieval, scoping, and access logging now enforce tenant ownership against the bundle's canonical request instead of trusting `bundle_id` alone
   - live validation now covers context bundle assemble/read/scope/access-log plus tenant-mismatch rejection for a Dynamo-backed request
   - data governance classification and lineage for request/artifact entities now validate canonical ownership instead of trusting caller-supplied tenant context
   - live validation now covers request classification, artifact classification, request->artifact lineage creation, lineage readback, and tenant-mismatch rejection for request classification
   - event replay and checkpoint access for request/run/artifact/promotion scopes now validate canonical ownership before reading events or persisting checkpoints
   - live validation now covers request-scope replay, checkpoint read/save, event lineage, and tenant-mismatch rejection for request replay
   - collaboration mode reads now validate canonical request ownership instead of treating cross-tenant requests as implicit `human_led` defaults
   - live validation now covers current-mode read, mode switch, transition listing, and tenant-mismatch rejection for collaboration mode access
   - workspace id-based reads and lifecycle operations now validate canonical request ownership instead of trusting `workspace_id` alone
   - live validation now covers workspace create/read/list/protected-target guard/merge plus tenant-mismatch rejection for workspace access
   - workflow execution id-based reads and command operations now validate canonical request ownership instead of trusting `execution_id` alone
   - live validation now covers workflow create/read/pause/resume/cancel plus tenant-mismatch rejection for workflow execution access
   - projection sync/update/conflict detection and reconciliation resolution now validate tenant ownership of the underlying projected entity instead of trusting `projection_id` alone
   - live validation now covers request projection create/sync/external-state update/conflict detection/resolution plus tenant-mismatch rejection for projection control-plane access
   - projection creation now validates canonical ownership of request/artifact entities before integration lookup, so wrong-tenant entity projections fail closed instead of creating orphaned mappings
   - live validation now covers artifact projection creation plus wrong-tenant request/artifact projection rejection
   - queue-routing recommendation, request escalation listing, and SLA evaluation now fail closed on inaccessible requests instead of returning empty/default summaries that masked tenant mismatch
   - live validation now covers same-tenant recommendation/SLA/escalation reads plus tenant-mismatch rejection for those request-owned queue-routing surfaces
   - planning membership creation and membership reads now validate canonical request ownership, preventing cross-tenant requests from being attached to a tenant's planning construct or echoed back through construct detail
   - live validation now covers same-tenant planning membership creation plus tenant-mismatch rejection for cross-tenant membership insertion
   - knowledge-context retrieval now validates canonical request ownership before returning tenant knowledge artifacts, preventing cross-tenant request ids from receiving tenant-scoped context results
   - live validation now covers same-tenant knowledge-context retrieval plus tenant-mismatch rejection at both the service and endpoint layers
   - event ledger and outbox request filters now validate canonical request ownership before returning tenant event pages, preventing cross-tenant request ids from collapsing into empty event timelines
   - live validation now covers same-tenant filtered event ledger/outbox reads plus tenant-mismatch rejection at both the service and endpoint layers
   - review queue request filters now validate canonical request ownership before returning tenant review pages, preventing cross-tenant request ids from collapsing into empty queue results
   - live validation now covers same-tenant filtered review queue reads plus tenant-mismatch rejection at both the service and endpoint layers
   - run list request filters now validate canonical request ownership before returning tenant run pages, preventing cross-tenant request ids from collapsing into empty run results
   - live validation now covers same-tenant filtered run-list reads plus tenant-mismatch rejection at both the service and endpoint layers
   - request list request-id filters now validate canonical request ownership before returning tenant request pages, preventing cross-tenant request ids from collapsing into empty request results
   - request-list endpoint handling for that filter path was also corrected to avoid the local `status` query parameter shadowing the FastAPI status helper during 404 translation
   - live validation now covers same-tenant filtered request-list reads plus tenant-mismatch rejection at both the service and endpoint layers
   - SLA breach request filters now validate canonical request ownership before returning tenant breach lists, preventing cross-tenant request ids from collapsing into empty breach results
   - live validation now covers same-tenant filtered SLA breach reads plus tenant-mismatch rejection at both the service and endpoint layers
   - event ledger artifact and promotion filters now validate canonical ownership before returning tenant event pages, preventing cross-tenant artifact/promotion ids from collapsing into empty event results
   - live validation now covers same-tenant filtered event ledger reads for artifacts and promotions plus tenant-mismatch rejection at both the service and endpoint layers
   - event ledger run filters now validate canonical ownership before returning tenant event pages, preventing cross-tenant run ids from collapsing into empty event results
   - live validation now covers same-tenant filtered event ledger reads for runs plus tenant-mismatch rejection at both the service and endpoint layers
   - event ledger check-run filters now validate canonical ownership before returning tenant event pages, preventing cross-tenant check-run ids from collapsing into empty event results
   - live validation now covers same-tenant filtered event ledger reads for check runs plus tenant-mismatch rejection at both the service and endpoint layers
   - promotion check-run streaming now also normalizes tenant mismatch to the same not-found path as the rest of the request-root event/query surfaces, instead of leaking a distinct forbidden branch for inaccessible promotions
   - admin projection control-plane endpoints now translate tenant-aware `projection_id` / projection-target failures into stable `404` responses instead of leaking unhandled service-layer `StopIteration` / `NoResultFound` exceptions as transport errors
   - integration-scoped admin projection/reconciliation reads now prove `integration_id` is in the caller's admin scope before querying, so inaccessible integrations return `404 Integration not found` instead of silently degrading into empty lists
   - platform-admin integration-scoped projection/reconciliation actions now resolve the integration's canonical tenant before querying downstream services, so cluster-wide admins no longer get false empty results from tenant-bound projection/reconciliation views
   - platform-admin projection-by-id actions now resolve the projection's canonical tenant before sync/update/resolve operations, so cluster-wide admins no longer get false not-found failures on valid projection control-plane actions
   - platform-admin request-root governance actions now resolve the request's canonical tenant before request detail, request projections, and agent-session/assignment operations, so cluster-wide admins no longer get false not-found failures on valid cross-tenant request control paths
   - platform-admin review and promotion control paths now resolve tenant scope from the underlying request-owned rows before review decisions/assignment overrides, promotion detail/actions, and promotion check-run reads, so cluster-wide admins no longer get false not-found failures on valid cross-tenant governance controls
   - platform-admin filtered query surfaces now normalize empty tenant scope correctly across request, run, review, event-ledger, and outbox filters, so request-scoped cross-tenant admin queries no longer fail with false not-found errors

9. Flip template reads to DynamoDB once parity is proven.
   Status:
   - backend selector added in `app/services/template_service.py`
   - `rgp-api` in `docker-compose.local.yml` now runs with `RGP_TEMPLATE_PERSISTENCE_BACKEND=dynamodb`
   - template routes verified live after container recreate

10. Flip request reads and writes to DynamoDB once parity is proven.
   Status:
   - backend selection now supports request lifecycle cutover
   - `rgp-api` in `docker-compose.local.yml` now runs with `RGP_REQUEST_PERSISTENCE_BACKEND=dynamodb`
   - live cutover verified for Dynamo-only request create/read, agent-session assignment, follow-up message posting, completion, and audit-history reads
   - runtime-dispatch-dependent request paths now validate successfully for Dynamo-only requests
   - broader end-to-end validation is still needed for the remaining SQL-backed projection-heavy paths and other non-canonical read models

## Phase 5: Runtime Migration

11. Introduce Lambda-compatible transport handlers for the core API surface.
   Status:
   - started
   - FastAPI app construction is now centralized in `apps/api/app/factory.py`
   - `apps/api/app/main.py` now uses the shared factory for the local `uvicorn` runtime
   - `apps/api/app/lambda_entrypoint.py` now provides a Lambda-compatible entrypoint using Mangum when the `aws` optional dependency is installed
   - runtime bootstrap is now centralized in `apps/api/app/runtime_bootstrap.py`, with guarded database/Dynamo slice initialization shared by both local `uvicorn` startup and the Lambda entrypoint
   - the local FastAPI runtime now uses a shared lifespan hook instead of embedding startup work directly in the app factory
   - the Lambda entrypoint now bootstraps explicitly and disables implicit ASGI lifespan handling, so Lambda no longer depends on FastAPI startup events firing implicitly
   - transport construction is now centralized in `apps/api/app/transport.py`, with both `app.main` and `app.lambda_entrypoint` reduced to thin aliases over the same shared ASGI app and Lambda-handler builder
   - operational entrypoints now point at the shared transport boundary as well: local docs/scripts and the Crew cluster `rgp-api` service now launch `uvicorn app.transport:get_asgi_app --factory` instead of `app.main:app`
   - local `uvicorn` now uses the shared transport builder in factory mode (`uvicorn app.transport:get_asgi_app --factory`), so both local HTTP and Lambda resolve through explicit transport functions instead of depending on a module-level app singleton
   - operational HTTP shell routes (`/healthz`, legacy docs/OpenAPI redirects) now live in `apps/api/app/transport.py` instead of `factory.py`, further separating transport concerns from the core application factory
   - OpenAPI/docs mount policy is now transport-owned as well: `apps/api/app/factory.py` builds the core app without docs/OpenAPI paths by default, and `apps/api/app/transport.py` applies the public HTTP shell shape (`/openapi.json`, `/docs`) when constructing the local/Lambda-facing app
   - HTTP middleware and exception-handling policy are now transport-owned too: CORS, correlation-id/tracing middleware, and HTTP/validation/unhandled exception envelopes were moved from `apps/api/app/factory.py` into `apps/api/app/transport.py`
   - startup lifespan/bootstrap policy is now transport-owned too: `apps/api/app/factory.py` accepts an optional lifespan hook, and `apps/api/app/transport.py` applies `runtime_lifespan()` when building the local/Lambda-facing app
   - `apps/api/app/lambda_entrypoint.py` now imports only `lambda_handler`, so the Lambda path no longer eagerly imports the module-level ASGI app just to expose the handler symbol
   - `apps/api/app/transport.py` no longer exports a module-level `app`; both local HTTP and Lambda now bind through explicit transport functions instead of relying on eager ASGI app construction at import time
   - `apps/api/app/main.py` no longer exports a module-level `app`; it now remains only as a thin alias module exporting the shared transport builder for any legacy imports that still need the symbol namespace
   - local validation after the refactor: `/healthz` returned `200` and `/docs` returned `200`

12. Keep a local HTTP shell only as a development adapter over the same handler layer.

13. Replace Postgres-backed local startup in the Crew cluster with DynamoDB Local once the first canonical slices are migrated.

## Immediate Rule

Until migration completes:
- new service code must depend on persistence ports
- new SQLAlchemy session usage should be treated as architectural debt
- new relational schema expansion should be avoided unless it is required for transition safety
