# RGP Persistence Inventory

This document captures the remaining relational-persistence coupling in RGP after the first service-boundary remediation pass.

## Snapshot

- Direct `SessionLocal()` usages remaining in `app/services` and `app/repositories`: `223`
- Direct repository imports remaining in `app/services`: `0`
- Largest single hotspot: `apps/api/app/repositories/governance_repository.py` with `86` `SessionLocal()` call sites

## Classification

### 1. Core Governance And Request Lifecycle

These files are closest to the canonical workflow/request state that should ultimately live in DynamoDB.

Files:
- `apps/api/app/repositories/governance_repository.py` (`86`)
- `apps/api/app/services/workflow_engine_service.py` (`8`)
- `apps/api/app/services/planning_service.py` (`9`)
- `apps/api/app/services/queue_routing_service.py` (`11`)
- `apps/api/app/services/sla_enforcement_service.py` (`6`)
- `apps/api/app/services/change_set_service.py` (`6`)
- `apps/api/app/services/workspace_service.py` (`6`)
- `apps/api/app/services/dependency_execution_service.py` (`1`)
- `apps/api/app/services/check_dispatch_service.py` (`1`)
- `apps/api/app/services/saga_orchestration_service.py` (`4`)

Access pattern characteristics:
- request and workflow state transitions
- queue assignment and escalation decisions
- planning memberships and roadmap aggregation
- change-set mutation and workspace state
- frequent write + event append patterns in one SQL transaction
- operational list/read views over current state

Migration implication:
- this is the highest-priority canonical state surface
- `governance_repository.py` should be decomposed by aggregate, not ported wholesale

### 2. Templates, Reviews, Promotions, And Checks

These are already partially isolated at the service boundary, but still backed by the SQL monolith.

Files:
- `apps/api/app/services/request_service.py` (port-isolated)
- `apps/api/app/services/template_service.py` (port-isolated)
- `apps/api/app/services/governance_service.py` (port-isolated)
- `apps/api/app/repositories/request_lifecycle_repository.py` (delegating wrapper)
- `apps/api/app/repositories/promotion_repository.py` (delegating wrapper)

Access pattern characteristics:
- aggregate-root style records with event history
- status transitions and decision logging
- list/filter operations by tenant and status

Migration implication:
- this remains the best first DynamoDB vertical slice
- the service boundary is ready; the next work is a real DynamoDB adapter and parity verification

### 3. Knowledge, Content, And Editorial State

These services represent governed content and reusable knowledge assets. They are canonical state, but less central than requests/promotions.

Files:
- `apps/api/app/services/knowledge_service.py` (`8`)
- `apps/api/app/services/domain_pack_service.py` (`10`)
- `apps/api/app/services/context_bundle_service.py` (`5`)
- `apps/api/app/services/data_governance_service.py` (`6`)
- `apps/api/app/services/editorial_workflow_service.py` (`5`)
- `apps/api/app/services/content_projection_service.py` (`3`)

Access pattern characteristics:
- artifact/version lifecycle
- installation/activation flows
- lineage and governance metadata
- editorial review state

Migration implication:
- candidate for a later aggregate family after request/workflow slices
- likely needs object-storage references for large bundle or artifact payloads

### 4. External Projection, Integration, And Reconciliation

These are partially canonical and partially derived/projection-oriented.

Files:
- `apps/api/app/services/projection_service.py` (`6`)
- `apps/api/app/services/reconciliation_service.py` (`4`)
- `apps/api/app/services/view_projection_service.py` (`5`)
- `apps/api/app/services/relationship_graph_service.py` (`3`)
- `apps/api/app/services/adapter_registry_service.py` (`3`)
- `apps/api/app/services/deployment_environment_service.py` (`4`)

Access pattern characteristics:
- external-id mapping
- projection synchronization
- reconciliation logs
- graph-like traversal and view assembly

Migration implication:
- projection mappings may fit canonical DynamoDB items
- graph/view-heavy reads may be better handled by projection tables or derived read models

### 5. Operational Policy, Security, And Replay

These are operational/stateful but not the main governance workflow domain.

Files:
- `apps/api/app/services/policy_engine_service.py` (`4`)
- `apps/api/app/services/security_hardening_service.py` (`2`)
- `apps/api/app/services/event_replay_service.py` (`4`)
- `apps/api/app/services/idempotency_service.py` (`2`)
- `apps/api/app/services/performance_metrics_service.py` (`2`)
- `apps/api/app/services/collaboration_mode_service.py` (`3`)
- `apps/api/app/services/billing_service.py` (`6`)

Access pattern characteristics:
- policy evaluation and enforcement records
- replay/checkpoint state
- idempotency and operational protections
- metrics and usage accounting

Migration implication:
- idempotency should likely move to its own DynamoDB table early
- metrics may be better kept as projection/telemetry data rather than canonical item state

## Transaction Shapes To Preserve

The relational code repeatedly relies on patterns that need explicit redesign in DynamoDB:

- write row(s) and append an event in the same unit of work
- update current-state rows and then issue sorted read queries
- mutate membership/ordering lists in place
- perform status-machine transitions with guard checks
- assemble read models by traversing multiple SQL tables

For the migration, these should become:

- conditional writes
- append-only event items alongside current-state items
- projection updaters for sorted list views
- idempotent command handling
- read-model tables or derived projections where joins were previously used

## Recommended Next DynamoDB Slices

1. Template versions
- already port-isolated
- aggregate shape is relatively clean

2. Request lifecycle
- already port-isolated
- central to the rest of the governance surface

3. Promotions / reviews / check runs
- already port-isolated through promotion/request lifecycle adapters
- naturally adjacent to requests

4. Workflow executions and queue routing
- important next because they underpin orchestration and assignment
- should follow once request/promotion aggregates have item shapes defined

## Immediate Rule

Until these slices are migrated:

- do not add new direct `SessionLocal()` usage to service code
- do not add new repository imports to service code
- new persistence work should be introduced behind ports/adapters only
