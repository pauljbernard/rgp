---
title: FlightOS Instructional Governance Contract
permalink: /api/flightos-instructional-governance/
section: API Contract
summary: Shared API contract for stage-aware instructional governance between FlightOS and RGP.
source_path: docs/api/flightos-instructional-governance-contract.md
---

# FlightOS Instructional Governance Contract

## Purpose

This document defines the minimum shared `rgp` API contract required for FlightOS instructional workflows to move from request-level authority to true stage-level shared governance.

The goal is to let FlightOS:

- submit governed instructional review requests into `rgp`
- read stage-aware workflow state from `rgp`
- send reviewer decisions into `rgp`
- keep CMS UI presentation local without retaining a second workflow engine

## Problem Statement

FlightOS instructional workflows currently expose a stage-based CMS review model with:

- ordered review stages
- stage-level approve or request-changes actions
- current-stage tracking
- release gating based on workflow state

`rgp` currently exposes request-level lifecycle state such as:

- `under_review`
- `changes_requested`
- `approved`
- `promotion_pending`
- `promoted`
- `completed`

That is sufficient for request authority, but not sufficient to drive FlightOS stage-based CMS review UX honestly.

## Non-Negotiable Rules

- `rgp` remains authoritative for workflow runtime and reviewer decision state.
- FlightOS may project and render workflow state, but shall not persist standalone shared-governance stage state.
- FlightOS may compute product-specific release-safety views locally, but those views must be reproducible from shared request and projection data.
- Shared mode must not silently fall back to FlightOS-local stage mutation.

## Scope

This contract is limited to FlightOS instructional workflows backed by:

- `tmpl_assessment@1.4.0`
- `tmpl_curriculum@3.1.0`

It does not define a general-purpose stage engine for every `rgp` request type. It defines a shared governance projection and command surface for the instructional review flow FlightOS already exposes.

## Canonical Identity

Every FlightOS instructional request submitted to `rgp` must include:

```json
{
  "input_payload": {
    "flightos_content_entry_id": "entry-assessment-grade5-fractions-checkpoint"
  }
}
```

Optional but recommended linkage fields:

```json
{
  "input_payload": {
    "flightos_content_entry_id": "entry-course-grade5-fractions",
    "flightos_schema_id": "course",
    "flightos_actor_user_id": "user-42"
  }
}
```

`flightos_content_entry_id` is the required join key for FlightOS workflow projection.

## Shared Projection Model

Add the following models in `rgp`:

- `InstructionalWorkflowStageRecord`
- `InstructionalWorkflowProjectionRecord`
- `InstructionalWorkflowProjectionListResponse`
- `InstructionalWorkflowDecisionRequest`

Recommended file:

- `/Volumes/data/development/rgp/apps/api/app/models/governance.py`

### `InstructionalWorkflowStageRecord`

```json
{
  "stage_id": "INSTRUCTIONAL_DESIGN_REVIEW",
  "label": "Instructional Design Review",
  "status": "PENDING",
  "required": true,
  "sequence": 1,
  "decision": null,
  "decided_at": null,
  "decided_by_user_id": null,
  "notes": null
}
```

Fields:

- `stage_id`: enum
- `label`: string
- `status`: `PENDING | ACTIVE | APPROVED | CHANGES_REQUESTED | SKIPPED`
- `required`: boolean
- `sequence`: integer
- `decision`: `APPROVE | REQUEST_CHANGES | null`
- `decided_at`: ISO timestamp or null
- `decided_by_user_id`: string or null
- `notes`: string or null

### `InstructionalWorkflowProjectionRecord`

```json
{
  "request_id": "req_200",
  "tenant_id": "cms-platform",
  "flightos_content_entry_id": "entry-assessment-grade5-fractions-checkpoint",
  "flightos_schema_id": "assessment",
  "template_id": "tmpl_assessment",
  "template_version": "1.4.0",
  "title": "Assessment Revision: Grade 5 Fractions Checkpoint",
  "request_status": "under_review",
  "workflow_status": "IN_REVIEW",
  "content_kind": "ASSESSMENT",
  "current_stage_id": "SME_REVIEW",
  "submitted_at": "2026-04-09T16:00:00.000Z",
  "submitted_by_user_id": "user-42",
  "approved_for_release_at": null,
  "released_at": null,
  "stages": []
}
```

Fields:

- `request_id`: shared `rgp` request id
- `tenant_id`: tenant id
- `flightos_content_entry_id`: required join key
- `flightos_schema_id`: `course | assessment | null`
- `template_id`: request template id
- `template_version`: request template version
- `title`: workflow title
- `request_status`: raw `rgp` request status
- `workflow_status`: FlightOS-compatible normalized status
  - `NOT_SUBMITTED`
  - `IN_REVIEW`
  - `CHANGES_REQUESTED`
  - `APPROVED_FOR_RELEASE`
  - `RELEASED`
- `content_kind`: `CURRICULUM_COURSE | ASSESSMENT`
- `current_stage_id`: stage enum or null
- `submitted_at`: ISO timestamp or null
- `submitted_by_user_id`: string or null
- `approved_for_release_at`: ISO timestamp or null
- `released_at`: ISO timestamp or null
- `stages`: ordered array of `InstructionalWorkflowStageRecord`

### `InstructionalWorkflowProjectionListResponse`

Use standard paginated list format:

```json
{
  "items": [],
  "page": 1,
  "page_size": 25,
  "total_count": 1,
  "total_pages": 1
}
```

## Stage Definitions

### Assessment

Ordered stages:

1. `INSTRUCTIONAL_DESIGN_REVIEW`
2. `SME_REVIEW`
3. `ASSESSMENT_REVIEW`
4. `CERTIFICATION_COMPLIANCE_REVIEW`

### Curriculum

Ordered stages:

1. `INSTRUCTIONAL_DESIGN_REVIEW`
2. `SME_REVIEW`
3. `CERTIFICATION_COMPLIANCE_REVIEW`

These stage definitions should be derived from template-specific instructional governance rules in `rgp`, not from FlightOS-local runtime state.

## Read Endpoints

Recommended file:

- `/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py`

### List instructional workflow projections

`GET /api/v1/requests/instructional-workflows`

Query params:

- `page`
- `page_size`
- `flightos_content_entry_id`
- `template_id`
- `workflow_status`

Response:

- `PaginatedResponse[InstructionalWorkflowProjectionRecord]`

Behavior:

- filters to instructional templates only
- returns stage-aware workflow projection records
- supports FlightOS list and summary read models

### Get instructional workflow projection by request id

`GET /api/v1/requests/{request_id}/instructional-workflow`

Response:

- `InstructionalWorkflowProjectionRecord`

### Optional convenience read by content entry id

`GET /api/v1/requests/instructional-workflows/by-content-entry/{flightos_content_entry_id}`

Response:

- `InstructionalWorkflowProjectionRecord`

This is optional. FlightOS can work with the list endpoint if the join key is queryable.

## Decision Command Endpoint

Recommended file:

- `/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py`

### Request body

```json
{
  "stage_id": "SME_REVIEW",
  "decision": "APPROVE",
  "notes": "Ready for compliance review."
}
```

Model:

```json
{
  "stage_id": "INSTRUCTIONAL_DESIGN_REVIEW | SME_REVIEW | ASSESSMENT_REVIEW | CERTIFICATION_COMPLIANCE_REVIEW",
  "decision": "APPROVE | REQUEST_CHANGES",
  "notes": "optional string"
}
```

### Endpoint

`POST /api/v1/requests/{request_id}/instructional-workflow/decisions`

Response:

- `InstructionalWorkflowProjectionRecord`

Behavior:

- validates that the request is an instructional request type
- validates that the submitted `stage_id` matches the currently active stage
- records the decision with actor and timestamp
- advances the next required stage on `APPROVE`
- moves the workflow to `CHANGES_REQUESTED` on `REQUEST_CHANGES`
- updates underlying request lifecycle state consistently

## Required Request Lifecycle Mapping

The projection should map request lifecycle state into FlightOS workflow state as follows.

| RGP request status | FlightOS workflow status |
| --- | --- |
| `draft` | `NOT_SUBMITTED` |
| `submitted` | `IN_REVIEW` |
| `validated` | `IN_REVIEW` |
| `classified` | `IN_REVIEW` |
| `ownership_resolved` | `IN_REVIEW` |
| `planned` | `IN_REVIEW` |
| `queued` | `IN_REVIEW` |
| `in_execution` | `IN_REVIEW` |
| `awaiting_review` | `IN_REVIEW` |
| `under_review` | `IN_REVIEW` |
| `changes_requested` | `CHANGES_REQUESTED` |
| `approved` | `APPROVED_FOR_RELEASE` |
| `promotion_pending` | `APPROVED_FOR_RELEASE` |
| `promoted` | `RELEASED` |
| `completed` | `RELEASED` |
| `failed` | `CHANGES_REQUESTED` |
| `rejected` | `CHANGES_REQUESTED` |

## Repository and Service Changes In `rgp`

### Add projection and decision models

File:

- `/Volumes/data/development/rgp/apps/api/app/models/governance.py`

Add:

- stage enums reused or mirrored for instructional workflow projection
- `InstructionalWorkflowStageRecord`
- `InstructionalWorkflowProjectionRecord`
- `InstructionalWorkflowDecisionRequest`

### Add endpoint handlers

File:

- `/Volumes/data/development/rgp/apps/api/app/api/v1/endpoints/requests.py`

Add:

- list projection route
- detail projection route
- decision command route

### Add service methods

File:

- `/Volumes/data/development/rgp/apps/api/app/services/request_service.py`

Add:

- `get_instructional_workflow_projection(...)`
- `list_instructional_workflow_projections(...)`
- `decide_instructional_workflow_stage(...)`

### Add persistence and transition logic

File:

- `/Volumes/data/development/rgp/apps/api/app/repositories/governance_repository.py`

Add:

- instructional stage projection builder
- request-to-stage mapping logic for `tmpl_assessment` and `tmpl_curriculum`
- stage-decision mutation logic
- transition side effects that keep request lifecycle and stage projection aligned

### Validate state transitions

File:

- `/Volumes/data/development/rgp/apps/api/app/domain/state_machine.py`

Likely no new top-level request statuses are required. The missing piece is stage projection and decision handling layered on top of existing request states.

## FlightOS Integration Target

Once the `rgp` contract above exists, FlightOS should update:

- `/Volumes/data/development/FlightOS/FlightOS/apps/api-server/src/platform/flightosRgpGateway.ts`
- `/Volumes/data/development/FlightOS/FlightOS/apps/api-server/src/server.ts`

Replace:

- current request-status overlay logic
- current shared-mode `409` block on stage decisions

With:

- reads from instructional workflow projection endpoints
- stage decision command to `POST /api/v1/requests/{request_id}/instructional-workflow/decisions`

## Acceptance Criteria

- FlightOS instructional workflow detail can be rendered entirely from shared `rgp` projection data plus local release-safety computation.
- FlightOS instructional workflow list and summary no longer infer stage state from coarse request status alone.
- Shared mode stage decisions no longer call FlightOS-local `decideStage`.
- A reviewer decision in FlightOS mutates shared `rgp` state and is visible immediately through the projection read API.
- The contract works for both `tmpl_assessment` and `tmpl_curriculum`.
