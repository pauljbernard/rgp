---
title: Gap Analysis
permalink: /reports/gap-analysis/
section: Reports
summary: Full codebase review against the constitution and requirements, documenting implemented, partial, and missing capability areas.
source_path: docs/gap-analysis-2026-04-03.md
---

# RGP Gap Analysis: Constitution & Requirements v8.0 vs. Implementation

**Date:** 2026-04-03 (updated 2026-04-03)
**Scope:** Full codebase review against constitution.md and requirements.md (both v8.0)

## ALL FOUR PHASES COMPLETE

### Phase 4 (Operational Maturity) — COMPLETE

Phase 4 delivered 10 iterations with 4 migrations (0037-0040) adding 13 new tables, 4 Pydantic model files, 8 service files, and 20 new tests. Key deliverables:

| Area | Tables | Service | Key Capability |
|------|--------|---------|----------------|
| **Data Governance** | `data_classifications`, `retention_policies`, `data_lineage_records` | `data_governance_service.py` | Classification, residency, retention, lineage tracking |
| **Billing & Quotas** | `usage_meters`, `quota_definitions` | `billing_service.py` | Usage metering, cost attribution, quota enforcement, budget control |
| **Queue & Assignment** | `assignment_groups`, `escalation_rules` | `queue_routing_service.py` | Skill/capacity routing, escalation engine, workload balancing |
| **SLA/SLO Enforcement** | `sla_definitions`, `sla_breach_audit` | `sla_enforcement_service.py` | Business SLA definitions, compliance evaluation, breach audit |
| **Security Hardening** | — | `security_hardening_service.py` | Prompt injection protection, context boundaries, execution limits |
| **Event Replay** | `event_replay_checkpoints` | `event_replay_service.py` | Event replay, checkpoint management, lineage tracing |
| **Multi-View Projections** | `view_definitions` | `view_projection_service.py` | Board, graph, roadmap views as canonical projections |
| **Deployment Modes** | `deployment_environments` | `deployment_environment_service.py` | SaaS/private/hybrid/air-gapped, environment isolation |

## Phases 1-3 Implementation Status: COMPLETE

### Phase 3 (Vertical Extension) — COMPLETE

Phase 3 delivered 10 iterations with 5 Alembic migrations (0032-0036) adding 12 new tables, 5 Pydantic model files, 7 service files, and 17 new tests. Key deliverables:

| Area | Tables | Service | Models |
|------|--------|---------|--------|
| **Domain Packs** | `domain_packs`, `domain_pack_installations` | `domain_pack_service.py` | `models/domain_pack.py` |
| **Workspaces & Change Sets** | `workspaces`, `change_sets` | `workspace_service.py`, `change_set_service.py` | `models/workspace.py` |
| **Editorial Workflows** | `editorial_workflows`, `content_projections` | `editorial_workflow_service.py`, `content_projection_service.py` | `models/editorial.py` |
| **Knowledge Artifacts** | `knowledge_artifacts`, `knowledge_artifact_versions` | `knowledge_service.py` | `models/knowledge.py` |
| **Planning Constructs** | `planning_constructs`, `planning_memberships` | `planning_service.py` | `models/planning.py` |

### Phase 2 (Core Governance) — COMPLETE

Phase 2 delivered 15 iterations with 5 migrations (0027-0031) adding 10 tables + 2 columns, plus policy DSL, check registry, MCP tool registry, collaboration modes, context bundles, saga orchestration, projection/reconciliation, and adapter registry.

## Phase 1 Implementation Status: COMPLETE

Phase 1 (Foundation) has been fully implemented with 13 iterations, 165 passing tests, and 0 regressions. Key deliverables:

| Deliverable | Files Created |
|------------|--------------|
| State machine domain module | `app/domain/state_machine.py` |
| Template engine domain module | `app/domain/template_engine.py` |
| Substrate abstraction layer | `app/domain/substrate/` (7 files: contracts, canonical models, HTTP adapters, event normalizer) |
| Domain-scoped repositories | `request_lifecycle_repository.py`, `promotion_repository.py`, `analytics_repository.py`, `org_repository.py`, `event_query_repository.py` |
| Workflow execution engine | Migration 0026 (3 new tables), `app/models/workflow.py`, `app/services/workflow_engine_service.py` |
| Async processing | `app/services/async_dispatch_service.py`, 3 new Celery tasks in worker |
| Seed data decoupling | `app/db/seed.py`, empty governance_repository constructor |
| Dead code removal | Deleted `request_repository.py`, `template_repository.py` |

Governance service now routes through domain-scoped repositories instead of calling the monolith directly.

---

## Fully Implemented

| Area | Evidence | Notes |
|------|----------|-------|
| Request Lifecycle | 21 statuses, full state machine in `governance_repository.py` | Filtering, pagination, SLA risk fields |
| Template Management | CRUD, versioning, validate, publish/deprecate | API + admin UI pages |
| Multi-Tenant Architecture | `TenantTable`, `OrganizationTable`, `TeamTable`, `UserTable` | Tenant → Org → Team → User hierarchy with `tenant_id` isolation |
| Event Sourcing | `EventStoreTable` + `EventOutboxTable` | Actor, detail, payload, timestamps; publisher integration |
| SLA/SLO Tracking | `sla_policy_id`, `sla_risk_level`, `sla_risk_reason` on requests | SLO summaries on routes via `performance_metrics_service.py` |
| Workflow Intelligence & Analytics | Lead time, cycle time, bottleneck detection, DORA metrics, cost analytics | Dedicated analytics pages: workflows, bottlenecks, performance, cost, delivery |
| Decision Traceability | `evidence` field on `CheckResultTable`; `RequestEventTable` with reason/evidence | Full event sourcing with actor attribution |
| Unified Timeline | History page aggregating events, runs, artifacts, reviews, promotions | `requests/[id]/history/page.tsx` |
| Review Queue | `ReviewQueueTable` with blocking status, assignment, decisions | Queue page + backend endpoints |
| Agent Integration | Multi-provider (OpenAI, Anthropic, Copilot) via `agent_provider_service.py` | Streaming, sessions, transcript management |
| Artifact Versioning | `ArtifactTable`, `ArtifactLineageEdgeTable`, `ArtifactEventTable` | Version tracking with lineage |
| Performance Metrics | `PerformanceMetricTable`, route summaries, P95 latency, Apdex | Trend analysis by day |
| Auth & Identity | Local accounts, registration, password reset, RBAC fields | Login, register, callback pages |

---

## Partially Implemented

### Relationship Graph
- **What exists:** `request_relationships` table (migration `20260330_0002`), `RequestRelationshipTable` model with source/target IDs and typed relationships
- **What's missing:** Graph traversal utilities, impact analysis, dependency-aware navigation, workflow constraint enforcement based on relationships
- **Requirements gap:** FR-REL-003 (traversal), FR-REL-004 (impact analysis), FR-REL-005 (workflow constraints)

### Collaboration Modes
- **What exists:** `AgentSessionTable` with `awaiting_human` flag, live session UI (`live-session.tsx`), agent session resume status
- **What's missing:** Explicit mode tracking (human-led / agent-assisted / agent-led), governed mode transitions, policy constraints by request type/role/substrate
- **Requirements gap:** FR-COL-001 through FR-COL-004

### Homoiconic Capabilities
- **What exists:** `CapabilityTable` with status tracking, `list_capabilities()` and `get_capability()` in governance service
- **What's missing:** Promotion-to-active lifecycle, self-evolution loop (requests → artifacts → capabilities → executable), version pinning, rollback
- **Requirements gap:** FR-HOMO-001 through FR-HOMO-006

### Knowledge Artifacts
- **What exists:** `ArtifactTable` with versioning, `ArtifactLineageEdgeTable` for lineage
- **What's missing:** Persistent knowledge base, retrieval into context bundles, agent consumption, reuse with lineage tracking
- **Requirements gap:** FR-KNOW-001 through FR-KNOW-005

### Policy Engine
- **What exists:** `policy_check_service.py` with 3 request checks (Intake Completeness, Review Package Readiness, Approval Freshness) and 2 promotion checks (Policy Bundle, Approval Freshness)
- **What's missing:** Custom check type registration, policy DSL, externalized policy engine, routing/branching/escalation policies, policy-driven orchestration
- **Requirements gap:** FR-POL-001 through FR-POL-004, plus policy-driven orchestration (FR-POL-005 through FR-POL-008)

### Promotion
- **What exists:** Dry-run, authorize, execute flow in `governance_repository.apply_promotion_action()`; deployment integration
- **What's missing:** Configurable promotion strategies (only one exists), multi-target promotion (code, content, service, config, knowledge), blue-green/canary/rolling
- **Requirements gap:** FR-PROM-003 (configurable strategies), FR-PROM-006 (multi-target)

### Template Authoring
- **What exists:** API endpoints for create/edit/validate/preview/publish/deprecate
- **What's missing:** Templates are bootstrapped from hard-coded demo data in `governance_repository.__init__()`; no dynamic schema loading, no real draft-edit-validate-preview-publish authoring cycle in production use
- **Requirements gap:** FR-TMPL-009 through FR-TMPL-013 (authoring surface)

### Worker / Async Processing
- **What exists:** Celery setup with Redis backend, `rgp.run_check_run` task
- **What's missing:** Most work executes synchronously in-request; no async promotion, deployment, analytics aggregation, or event processing jobs
- **Requirements gap:** Execution constitution requires async orchestration

---

## Not Implemented

### HIGH Impact

| Area | Constitution/Requirements Reference | Description |
|------|--------------------------------------|-------------|
| **Domain Packs** | Section 28, FR-ECO-004 through FR-ECO-010 | Installable packs for Source Control, ITSM, Content/Editorial, Planning, Knowledge with templates, artifact types, workflows, policies, lifecycle variants, analytics, views. Core extensibility model for multi-vertical support. |
| **Federated Governance** | Section 20, FR-FED-001 through FR-FED-007 | Bidirectional sync between canonical RGP state and external systems. Projection model, reconciliation, conflict resolution, adapter contracts. Multiple simultaneous external integrations. |
| **MCP / Context Bundle Integration** | Section 22, FR-MCP-001 through FR-MCP-012 | Governed context access for agents: tool invocation, capability discovery, least-privilege scoping. Context bundles include request data, template semantics, workflow state, policy constraints, knowledge artifacts, relationship graph. |
| **Cross-Request Orchestration** | FR-XRO-001 through FR-XRO-006 | Saga-style coordination across related requests. Compensation and rollback-aware orchestration. Cross-system dependency coordination. Visible and auditable cross-request state. |
| **Substrate Abstraction** | FR-SUB-001 through FR-SUB-005 | Pluggable adapter layer for multiple substrate types (source control, content, ITSM, planning). Canonical representations for repositories, documents, records, change sets, managed targets. Event normalization. |
| **Workspace & Change Management** | FR-WCM-001 through FR-WCM-008 | Isolated workspace creation, change set management, diff/lineage metadata, protected target enforcement. Applicable to any artifact/record type, not just code. |

### MEDIUM Impact

| Area | Constitution/Requirements Reference | Description |
|------|--------------------------------------|-------------|
| **Content & Editorial Workflows** | FR-CED-001 through FR-CED-006 | Content-oriented artifact types, multi-stage editorial workflows, content revision branching, multi-channel projection, editorial roles (author, editor, fact reviewer, legal, compliance, publisher). |
| **Data Governance** | FR-DG-001 through FR-DG-004 | Data classification, residency rules, retention policies, data lineage tracking. Required for compliance. |
| **Dependency-Aware Execution** | FR-DEP-001 through FR-DEP-004 | Execution sequencing based on relationships, blocking when dependencies unmet, parallel execution when permitted, dependency-aware retry and recovery. |
| **Queue & Assignment (Advanced)** | FR-QAS-002 through FR-QAS-006 | Routing by skill, role, capacity, workload, priority, SLA context, policy domain. Escalation rules. Queue-level analytics and workload visibility. Dynamic balancing. Only basic review queue currently exists. |
| **Security (Advanced)** | FR-SEC-001 through FR-SEC-005 | Execution isolation, prompt injection protection, secure secret management. Current integration_security_service handles basic credential encryption only. |
| **Adapter Contracts** | FR-OBS-006 through FR-OBS-011 | Binding, event ingestion, projection, promotion, reconciliation, capability discovery contracts for all external integrations. |

### LOW Impact

| Area | Constitution/Requirements Reference | Description |
|------|--------------------------------------|-------------|
| **Billing & Quotas** | FR-BQ-001 through FR-BQ-005 | Usage tracking, cost attribution, quota enforcement, rate limiting, budget controls. Cost analytics pages exist but no enforcement. |
| **Ecosystem / Registry** | FR-ECO-001 through FR-ECO-003 | Reusable components, versioned publishing, capability discovery marketplace. |
| **Multi-View Projections** | FR-MVP-001 through FR-MVP-003 | Board, graph, planning/roadmap views. Some views exist (queue, timeline, data tables) but board, graph, and roadmap views are absent. |
| **Deployment Modes** | FR-DEP-001 through FR-DEP-003 | SaaS, private, hybrid, air-gapped deployment. Current deployment_service is HTTP-only. |
| **Event Replay** | FR-OBS-009, FR-OBS-010 | Event replay support, lineage from substrate event to governance outcome. Events are stored but no replay mechanism. |

---

## Architectural Concerns

### 1. Demo-Seeded Data
`governance_repository.__init__()` (line ~193) bootstraps ALL data from `seed_requests()`, `seed_templates()`, and related seed functions in `governance.py`. The system operates as a demo sandbox with hard-coded curriculum data rather than a persistent production store.

### 2. Monolithic Repository
All governance business logic lives in `governance_repository.py` (~1600+ lines). The service layer (`governance_service.py`, `request_service.py`, `template_service.py`) is a thin pass-through facade with zero business logic. This creates a single point of complexity and makes testing governance rules in isolation difficult.

### 3. Hard-Coded State Machine
Request lifecycle transition rules and SLA policies are defined as class-level constants in the repository. They are not configurable per template or tenant, which conflicts with the constitution's requirement for extensible lifecycle with custom states, transitions, and role-based constraints (FR-WBD-006).

### 4. No Workflow Execution Engine
Templates reference `workflow_binding_id` but no actual workflow runtime exists. The constitution's Execution Plane (Foundry integration, step-level orchestration, pause/resume/cancel/retry) is represented only by the HTTP-based `runtime_dispatch_service.py` with no orchestration logic.

### 5. Frontend Stub Pages
Reviews (`/reviews`) and Promotions (`/promotions`) pages are redirects to sub-routes. Backend support exists for both, but the landing page experience is incomplete.

### 6. Synchronous Processing
Nearly all governance operations (check execution, promotion, deployment) run synchronously within API request handlers. The Celery worker handles only check runs. This will not scale for complex workflows or long-running operations.

---

## Prioritized Implementation Roadmap

### Phase 1: Foundation (blocks everything else)
1. **Substrate Abstraction Layer** — adapter contracts, canonical representations, event normalization
2. **Real Template Authoring** — dynamic schema loading, remove demo seed dependency
3. **Workflow Execution Engine** — step-level orchestration, pause/resume/cancel/retry
4. **Refactor Governance Repository** — extract state machine, policy engine, and promotion logic into focused services
5. **Async Processing** — move promotion, deployment, and complex checks to worker

### Phase 2: Core Governance
1. **Federated Governance** — projection model, bidirectional sync, reconciliation
2. **MCP-Style Context Bundles** — governed context assembly, scoping, audit
3. **Cross-Request Orchestration** — saga patterns, compensation, rollback
4. **Advanced Policy Engine** — custom check types, policy DSL, routing/branching/escalation
5. **Collaboration Mode Governance** — explicit mode tracking, governed transitions

### Phase 3: Vertical Extension
1. **Domain Pack Framework** — installation, activation, pack-to-core integration
2. **Content & Editorial Workflows** — editorial artifact types, multi-stage workflows
3. **Workspace & Change Management** — isolated workspaces, change sets, protected targets
4. **Knowledge Artifact Curation** — persistent knowledge base, retrieval, agent consumption
5. **Relationship Graph Completion** — traversal, impact analysis, constraint enforcement

### Phase 4: Operational Maturity
1. **Data Governance** — classification, residency, retention policies
2. **Billing & Quota Enforcement** — usage tracking, rate limiting, budgets
3. **Advanced Queue Routing** — skill/capacity/workload routing, escalation, dynamic balancing
4. **Security Hardening** — execution isolation, prompt injection protection
5. **Multi-View Projections** — board, graph, planning/roadmap views

---

## Summary Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| Fully Implemented | 13 areas | ~30% |
| Partially Implemented | 8 areas | ~18% |
| Not Implemented (High) | 6 areas | ~14% |
| Not Implemented (Medium) | 6 areas | ~14% |
| Not Implemented (Low) | 5 areas | ~11% |
| Architectural Concerns | 6 issues | — |

**Overall Assessment:** The RGP platform has a solid foundation — the request lifecycle, event sourcing, multi-tenancy, analytics, and agent integration are operational. However, the differentiating capabilities defined in the constitution (federated governance, substrate neutrality, domain packs, MCP integration, cross-request orchestration) remain unbuilt. The architecture needs refactoring (monolithic repository, synchronous processing, demo data) before these advanced features can be layered on effectively.
