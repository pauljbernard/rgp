---
title: Traceability Matrix
permalink: /reports/traceability-matrix/
section: Reports
summary: Traceability view mapping constitutional and requirements areas to live implementation status across code, API, UI, and tests.
source_path: docs/traceability-matrix-2026-04-03.md
---

# RGP Traceability Matrix: Constitution & Requirements v8.0 vs Current Build

**Date:** 2026-04-03  
**Purpose:** Map the current implementation to the constitutional and requirements surface so the remaining remediation work is explicit and actionable.

## Status Legend

- `Implemented`: present in code, exposed through live API/UI, and covered by tests
- `Partial`: present in code and/or data model, but not fully exposed, enforced, or tested
- `Spec Only`: defined in constitution/requirements, but not meaningfully integrated into the live product path

## Traceability Matrix

| Constitutional Area | Requirement Families | Primary Code Paths | API / UI Exposure | Test Coverage | Status | Notes |
|---|---|---|---|---|---|---|
| Request as the unit of governed work; canonical lifecycle | `FR-REQ-001` to `FR-REQ-007` | [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py), [/Volumes/data/development/rgp/apps/api/app/repositories/request_lifecycle_repository.py](/Volumes/data/development/rgp/apps/api/app/repositories/request_lifecycle_repository.py), [/Volumes/data/development/rgp/apps/web/app/requests](/Volumes/data/development/rgp/apps/web/app/requests) | Request list, create, detail, submit, amend, clone, supersede, history | [/Volumes/data/development/rgp/tests/integration/test_end_to_end_user_stories.py](/Volumes/data/development/rgp/tests/integration/test_end_to_end_user_stories.py), [/Volumes/data/development/rgp/apps/web/e2e/request-journeys.spec.ts](/Volumes/data/development/rgp/apps/web/e2e/request-journeys.spec.ts) | `Implemented` | This is the strongest part of the current system. |
| Template governance and authoring | `FR-TPL-*` | [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/admin.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/admin.py), [/Volumes/data/development/rgp/apps/web/app/admin/templates](/Volumes/data/development/rgp/apps/web/app/admin/templates), [/Volumes/data/development/rgp/apps/api/app/models/template.py](/Volumes/data/development/rgp/apps/api/app/models/template.py) | Admin template catalog and drill-down workbench | [/Volumes/data/development/rgp/apps/web/app/admin/templates/page.test.tsx](/Volumes/data/development/rgp/apps/web/app/admin/templates/page.test.tsx), [/Volumes/data/development/rgp/apps/web/app/admin/templates/[templateId]/[version]/page.test.tsx](/Volumes/data/development/rgp/apps/web/app/admin/templates/[templateId]/[version]/page.test.tsx), `US-01` | `Implemented` | Mature for current scope. |
| Review, approval, promotion, and request completion invariants | `FR-REV-*`, `FR-PRO-*` | [/Volumes/data/development/rgp/apps/api/app/repositories/promotion_repository.py](/Volumes/data/development/rgp/apps/api/app/repositories/promotion_repository.py), [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/reviews.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/reviews.py), [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/promotions.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/promotions.py), [/Volumes/data/development/rgp/apps/web/app/reviews](/Volumes/data/development/rgp/apps/web/app/reviews), [/Volumes/data/development/rgp/apps/web/app/promotions](/Volumes/data/development/rgp/apps/web/app/promotions) | Review queue and promotion pages | `US-05`, browser/admin journeys | `Implemented` | Promotion is operational, though strategy diversity is still limited. |
| Tenant / organization / team / user governance | `FR-REQ-008` to `FR-REQ-011`, org admin requirements | [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/admin.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/admin.py), [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/auth.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/auth.py), [/Volumes/data/development/rgp/apps/web/app/admin/org](/Volumes/data/development/rgp/apps/web/app/admin/org), [/Volumes/data/development/rgp/apps/web/app/register](/Volumes/data/development/rgp/apps/web/app/register) | Admin org pages, public registration, approval-based provisioning | [/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py](/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py), `US-02` | `Implemented` | Real hierarchy exists and is user-operable. |
| Analytics, observability, delivery intelligence | `FR-INTEL-*`, `FR-OBS-*`, `FR-SLA-*` | [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/analytics.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/analytics.py), [/Volumes/data/development/rgp/apps/web/app/analytics](/Volumes/data/development/rgp/apps/web/app/analytics), [/Volumes/data/development/rgp/apps/api/app/services/performance_metrics_service.py](/Volumes/data/development/rgp/apps/api/app/services/performance_metrics_service.py) | Workflow, agent, delivery, performance, bottleneck, cost pages | `US-06`, [/Volumes/data/development/rgp/tests/performance/test_performance_scalability.py](/Volumes/data/development/rgp/tests/performance/test_performance_scalability.py) | `Implemented` | Strong read-side reporting surface. |
| Agent assignment, persistent sessions, real-time interaction | `FR-AGT-001` to `FR-AGT-006`, `FR-INT-007` to `FR-INT-009` | [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py), [/Volumes/data/development/rgp/apps/api/app/services/agent_provider_service.py](/Volumes/data/development/rgp/apps/api/app/services/agent_provider_service.py), [/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents](/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents) | Agent assignment and session drill-down pages | `US-04`, browser request journey | `Implemented` | This is real and visible in the current product. |
| Governed context for agent assignment | `FR-AGT-007` to `FR-AGT-010`, `FR-CTX-*` | [/Volumes/data/development/rgp/apps/api/app/services/context_bundle_service.py](/Volumes/data/development/rgp/apps/api/app/services/context_bundle_service.py), [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py), [/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents/page.tsx](/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents/page.tsx), [/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents/[sessionId]/live-session.tsx](/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents/[sessionId]/live-session.tsx) | Request-level assignment preview, session context drill-down, governed mode/profile controls, context bundle visibility, access audit | [/Volumes/data/development/rgp/apps/web/app/coverage-smoke-pages.test.tsx](/Volumes/data/development/rgp/apps/web/app/coverage-smoke-pages.test.tsx), [/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py](/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py) | `Implemented` | Context bundles are now assembled, scoped, surfaced, consumed by providers, and visible in the live request agent journey. |
| MCP-governed context/tool access | `FR-MCP-*` | [/Volumes/data/development/rgp/apps/api/app/domain/mcp/registry.py](/Volumes/data/development/rgp/apps/api/app/domain/mcp/registry.py), [/Volumes/data/development/rgp/apps/api/app/domain/mcp/access_control.py](/Volumes/data/development/rgp/apps/api/app/domain/mcp/access_control.py), [/Volumes/data/development/rgp/apps/api/app/repositories/governance_repository.py](/Volumes/data/development/rgp/apps/api/app/repositories/governance_repository.py), [/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents/[sessionId]/live-session.tsx](/Volumes/data/development/rgp/apps/web/app/requests/[requestId]/agents/[sessionId]/live-session.tsx) | Session UI exposes available, restricted, and degraded capabilities plus turn-level MCP audit entries | [/Volumes/data/development/rgp/apps/web/app/coverage-smoke-pages.test.tsx](/Volumes/data/development/rgp/apps/web/app/coverage-smoke-pages.test.tsx), [/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py](/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py) | `Implemented` | MCP is now an operational first-class surface for agent sessions, including policy-scoped exposure and auditable turn-level capability decisions. |
| Substrate-neutral canonical model and adapter contracts | `FR-SUB-*`, `FR-ADP-*`, `FR-EVT-*` | [/Volumes/data/development/rgp/apps/api/app/domain/substrate](/Volumes/data/development/rgp/apps/api/app/domain/substrate), [/Volumes/data/development/rgp/apps/api/app/services/adapter_registry_service.py](/Volumes/data/development/rgp/apps/api/app/services/adapter_registry_service.py) | Current product has integrations and runtime/deployment adapters, but not a fully surfaced adapter registry or canonical substrate management UI/API | Unit tests for substrate primitives | `Partial` | The codebase now has a real substrate/domain layer, but product integration is still incomplete. |
| Federated governance, projection, synchronization, reconciliation | `FR-FED-*`, `FR-PROJ-*`, `FR-SYNC-*`, `FR-CONF-*` | [/Volumes/data/development/rgp/apps/api/app/services/projection_service.py](/Volumes/data/development/rgp/apps/api/app/services/projection_service.py), [/Volumes/data/development/rgp/apps/api/app/services/reconciliation_service.py](/Volumes/data/development/rgp/apps/api/app/services/reconciliation_service.py), [/Volumes/data/development/rgp/apps/api/app/models/federation.py](/Volumes/data/development/rgp/apps/api/app/models/federation.py), [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/admin.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/admin.py), [/Volumes/data/development/rgp/apps/web/app/admin/integrations/[integrationId]/page.tsx](/Volumes/data/development/rgp/apps/web/app/admin/integrations/[integrationId]/page.tsx) | Admin integration drill-down now exposes projection mappings, sync, reconciliation activity, and resolution actions | [/Volumes/data/development/rgp/apps/web/app/coverage-smoke-pages.test.tsx](/Volumes/data/development/rgp/apps/web/app/coverage-smoke-pages.test.tsx), [/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py](/Volumes/data/development/rgp/tests/integration/test_spec_compliance.py) | `Partial` | No longer backend-only; now operator-visible, but still lacks richer conflict workflows, external adapter callbacks, and broader federated timeline exposure. |
| Cross-system orchestration and saga support | `FR-ORCH-*`, federated orchestration | [/Volumes/data/development/rgp/apps/api/app/services/saga_orchestration_service.py](/Volumes/data/development/rgp/apps/api/app/services/saga_orchestration_service.py), [/Volumes/data/development/rgp/apps/api/app/models/saga.py](/Volumes/data/development/rgp/apps/api/app/models/saga.py) | No dedicated saga/orchestration routes or UI | Unit tests only, no routed integration coverage | `Partial` | Implemented as backend domain/service scaffolding, not productized. |
| Extensible lifecycle and workflow engine | `FR-LIFE-*`, execution orchestration | [/Volumes/data/development/rgp/apps/api/app/services/workflow_engine_service.py](/Volumes/data/development/rgp/apps/api/app/services/workflow_engine_service.py), [/Volumes/data/development/rgp/apps/api/app/models/workflow.py](/Volumes/data/development/rgp/apps/api/app/models/workflow.py), [/Volumes/data/development/rgp/apps/api/app/services/async_dispatch_service.py](/Volumes/data/development/rgp/apps/api/app/services/async_dispatch_service.py) | No explicit workflow-definition UI/API beyond current template binding fields | Unit tests only, no user-facing workflow engine management | `Partial` | Engine exists, but the live system still behaves primarily like a hard-wired governed lifecycle platform. |
| Queue and assignment model beyond review queue | `FR-QUE-*` | [/Volumes/data/development/rgp/apps/api/app/services/queue_routing_service.py](/Volumes/data/development/rgp/apps/api/app/services/queue_routing_service.py), queue tables in [/Volumes/data/development/rgp/apps/api/app/db/models.py](/Volumes/data/development/rgp/apps/api/app/db/models.py) | Review queue exists; generalized assignment-queue product surface does not | Limited backend tests, no general queue UI | `Partial` | Review queue is real, broad queue-routing model is not yet integrated into live product operations. |
| SLA/SLO enforcement as active governance control | `FR-SLA-*` | [/Volumes/data/development/rgp/apps/api/app/services/sla_enforcement_service.py](/Volumes/data/development/rgp/apps/api/app/services/sla_enforcement_service.py), analytics/performance pages | Analytics and risk views exist; explicit policy-driven SLA enforcement flows are not surfaced | Analytics/performance tests, no explicit enforcement journey | `Partial` | Strong observability, weaker active control-plane enforcement. |
| Domain packs | `FR-DOM-*` | [/Volumes/data/development/rgp/apps/api/app/services/domain_pack_service.py](/Volumes/data/development/rgp/apps/api/app/services/domain_pack_service.py), [/Volumes/data/development/rgp/apps/api/app/models/domain_pack.py](/Volumes/data/development/rgp/apps/api/app/models/domain_pack.py) | No domain pack routes or UI | Spec compliance only | `Spec Only` | Service exists, but nothing in the live API/router/web exposes domain pack lifecycle. |
| Planning constructs and roadmap views | `FR-PLAN-*`, `FR-VIEW-*` | [/Volumes/data/development/rgp/apps/api/app/services/planning_service.py](/Volumes/data/development/rgp/apps/api/app/services/planning_service.py), [/Volumes/data/development/rgp/apps/api/app/services/view_projection_service.py](/Volumes/data/development/rgp/apps/api/app/services/view_projection_service.py), [/Volumes/data/development/rgp/apps/api/app/models/planning.py](/Volumes/data/development/rgp/apps/api/app/models/planning.py) | No planning UI, no roadmap page, no board/graph pages | Unit tests only | `Spec Only` | Backend implementation work exists, but zero live product exposure. |
| Knowledge artifacts and governed reusable memory | `FR-KNOW-*` | [/Volumes/data/development/rgp/apps/api/app/services/knowledge_service.py](/Volumes/data/development/rgp/apps/api/app/services/knowledge_service.py), [/Volumes/data/development/rgp/apps/api/app/models/knowledge.py](/Volumes/data/development/rgp/apps/api/app/models/knowledge.py) | No knowledge routes, no knowledge admin/workbench UI, no visible retrieval into agent assignment | Spec compliance only | `Spec Only` | Present as code, absent as product. |
| Content/editorial workflows and projection | `FR-CONT-*`, multi-asset/editorial portions | [/Volumes/data/development/rgp/apps/api/app/services/editorial_workflow_service.py](/Volumes/data/development/rgp/apps/api/app/services/editorial_workflow_service.py), [/Volumes/data/development/rgp/apps/api/app/services/content_projection_service.py](/Volumes/data/development/rgp/apps/api/app/services/content_projection_service.py), [/Volumes/data/development/rgp/apps/api/app/models/editorial.py](/Volumes/data/development/rgp/apps/api/app/models/editorial.py) | No dedicated editorial/content UI or endpoints | Unit tests only | `Spec Only` | The product still presents as a governed request platform, not yet a live editorial operating surface. |
| Workspaces and generalized change sets | `FR-CODE-008`, workspace/change management | [/Volumes/data/development/rgp/apps/api/app/services/workspace_service.py](/Volumes/data/development/rgp/apps/api/app/services/workspace_service.py), [/Volumes/data/development/rgp/apps/api/app/services/change_set_service.py](/Volumes/data/development/rgp/apps/api/app/services/change_set_service.py), [/Volumes/data/development/rgp/apps/api/app/models/workspace.py](/Volumes/data/development/rgp/apps/api/app/models/workspace.py), [/Volumes/data/development/rgp/apps/web/app/workspaces/page.tsx](/Volumes/data/development/rgp/apps/web/app/workspaces/page.tsx) | Workspaces page exists, but the new generalized workspace/change-set backend is not clearly wired into request execution flows yet | Some UI presence, backend service tests limited | `Partial` | Surface exists, but the generalized substrate-neutral change-set model is not yet evidently driving the product. |
| Data governance | `FR-DAT-*` | [/Volumes/data/development/rgp/apps/api/app/services/data_governance_service.py](/Volumes/data/development/rgp/apps/api/app/services/data_governance_service.py), [/Volumes/data/development/rgp/apps/api/app/models/data_governance.py](/Volumes/data/development/rgp/apps/api/app/models/data_governance.py) | No data-governance API/UI surface | Unit tests only | `Spec Only` | Implemented as backend capability, not exposed. |
| Billing and quotas | `FR-BILL-*` | [/Volumes/data/development/rgp/apps/api/app/services/billing_service.py](/Volumes/data/development/rgp/apps/api/app/services/billing_service.py), [/Volumes/data/development/rgp/apps/api/app/models/billing.py](/Volumes/data/development/rgp/apps/api/app/models/billing.py) | Cost analytics exists; billing/quota management does not | Unit tests only | `Partial` | Reporting exists; enforcement/administration is not productized. |
| Unified timeline across federated systems | `FR-TIME-*` | Existing request history plus new federated spec; endpoint support still primarily request-local via [/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/events.py](/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/events.py) and request history | Request history and event ledger exist | `US-03`, `US-06` | `Partial` | Strong local timeline, not yet true cross-system federated timeline. |

## Integration Reality Check

The recent external-agent/backend expansion materially improved the codebase, but most of the new capability sits in one of four states:

1. `Integrated into live product`
- request lifecycle
- template workbench
- org administration
- reviews/promotions
- analytics
- agent sessions

2. `Backend-scaffolded but not routed`
- domain packs
- planning constructs
- knowledge artifacts
- saga orchestration
- queue routing
- SLA enforcement

3. `Modeled and migrated but not yet productized`
- editorial/content workflows
- billing/quota enforcement
- data governance
- multi-view board/graph/roadmap projections

4. `Specified but still weakly expressed in live runtime behavior`
- policy-driven collaboration mode changes beyond the request agent journey

## Actionable Remediation Plan

### Track 1: Make the New Backend Real

These areas already have enough backend structure that the next step should be product integration, not more domain scaffolding.

1. **Federation / Projection / Reconciliation**
- Add admin/API surfaces for projection mappings and reconciliation conflicts
- Expose reconciliation status in integration drill-down pages
- Add live workflows that project canonical entities into at least one external substrate and reconcile them back
  - Status: first operator-facing slice is implemented on admin integrations; remaining gap is richer conflict handling and broader cross-system visibility

2. **Planning / Knowledge / Domain Packs**
- Add first-class routes and pages
- Move these from pure backend capability into user-operable product flows

### Track 2: Convert Partial Control Logic into Active Governance

1. **Queue Routing**
- Promote generalized assignment queues beyond review queue only
- Expose routing basis: skill, workload, SLA, policy domain

2. **SLA Enforcement**
- Move from analytics/risk visibility into active escalation and blocking behavior

3. **Workflow Engine**
- Bind more request execution through the new workflow engine rather than primarily repository-driven hard-coded transitions

### Track 3: Close Spec/Product Drift

1. Add routed/API/UI traceability for:
- `FR-DOM-*`
- `FR-PLAN-*`
- `FR-KNOW-*`
- `FR-FED-*`
- `FR-PROJ-*`
- `FR-SYNC-*`
- `FR-CONF-*`
2. Extend the compliance suite so it checks not only document presence, but also:
- route exposure for major implemented capabilities
- service-to-endpoint integration for major new backend modules
- browser/API journeys for any area claimed as `Implemented`

## Recommended Next Milestone

The most leverage comes from treating this as an **integration milestone**, not another modeling milestone:

- **Milestone A:** Agent Context + MCP productization
  - Status: materially complete for the current request agent journey
- **Milestone B:** Federated projection/reconciliation productization
- **Milestone C:** Planning + knowledge + domain pack productization

If those three are completed, the build will begin to match the expanded v8.0 constitutional surface rather than merely anticipating it.
