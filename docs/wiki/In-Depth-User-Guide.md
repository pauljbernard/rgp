---
title: In-Depth User Guide
permalink: /wiki/in-depth-user-guide/
section: Wiki
summary: Detailed guide to requests, agent sessions, reviews, approvals, promotions, and deeper product behavior.
source_path: docs/wiki/In-Depth-User-Guide.md
---

# In-Depth User Guide

## 1. Working with Requests

Requests are the core governed object in RGP.

On a request detail page you can inspect:

- overview and status
- runs
- checks
- reviews
- promotions
- artifacts
- agent sessions
- timeline and event history

### Request Statuses

Common statuses include:

- Draft
- Submitted
- Validated
- Planned
- Queued
- In Execution
- Awaiting Input
- Awaiting Review
- Approved
- Promotion Pending
- Promoted
- Completed
- Failed

## 2. Agent Sessions

RGP supports assigning a request directly to an integrated agent.

### How It Works

1. open a request
2. navigate to the agent surface
3. choose an agent integration
4. start a session
5. interact across multiple turns
6. accept the response when you want the request to continue

### Important Behavior

- the session persists transcript and state
- agent output can stream live
- the request can pause in `awaiting_input`
- accepting the result resumes workflow

For governed external runtime sessions such as `sbcl-agent`, the session page also becomes a runtime-control surface.

Operators can now:

- inspect governed runtime environment, thread, and turn references
- see pending approval checkpoints exposed by the external runtime
- approve or resume specific runtime work-items
- import runtime-produced artifacts into RGP as first-class governed artifacts with lineage

That means an `sbcl-agent` session is not only a conversation transcript. It is a governed view over a durable external runtime.

This is intentionally different from a normal chatbot. The session is part of the governed work record.

## 3. Reviews and Approvals

Requests that require review move into the review queue.

Reviewers can:

- approve
- reject
- request changes
- use reassignment / override flows where allowed by governance

Promotion approval happens separately and remains explicit.

## 4. Promotions and Deployments

Promotion is the governed finalization step for work that must be formally advanced.

A promotion may include:

- preflight checks
- approver assignment
- deployment execution
- completion recording

Requests are not supposed to silently promote or complete without visible governance evidence.

## 5. Analytics

RGP includes several analytics families:

- workflow analytics
- agent analytics
- delivery analytics
- performance analytics
- cost analytics
- portfolio and organizational summaries

Most analytics pages support filtering by:

- portfolio
- team
- user
- time window

Several also support comparison views and time-series charts.

## 6. Admin Functions

### Templates

Use **Admin → Templates** to manage template identities and versions.

The drill-down workbench supports:

- draft creation
- field design
- conditional rules
- routing rules
- governance requirements
- validation
- preview
- comparison
- publish / deprecate

### Organization

Use **Admin → Organization** to manage:

- teams
- memberships
- users
- portfolios

The org page is built around a hierarchical team-membership view and drill-down management pages.

### Integrations

Use **Admin → Integrations** to manage:

- runtime and external system bindings
- direct-assignment agent integrations
- provider settings such as model, base URL, workspace, and secret rotation

Secrets are managed through the integrations surfaces but are intentionally not readable back in cleartext.

## 7. Operational Queues

Operational users should rely on the queue pages for active work:

- Review Queue
- Blocked Requests
- SLA Risk
- Promotion Pending

These are table-driven and intended for sorting, filtering, and action.

## 8. Troubleshooting

### Request Is Stuck

Check:

- status
- blocking checks
- pending review items
- promotion state
- agent session state

### Agent Session Is Not Progressing

Check:

- the selected integration
- session state
- whether the latest turn completed
- whether the request is waiting on human input
- whether a governed runtime approval checkpoint is blocking execution
- whether the runtime artifact or approval action you expect has already been reconciled into the session page

### Analytics Look Incomplete

Check whether the relevant request/run/review/promotion activity actually occurred. Analytics are derived from governed work records and performance telemetry.

## 9. Mental Model for Users

The most important thing to understand is:

- RGP is not mainly a chat app
- RGP is not mainly a dashboard
- RGP is a governed work system

If you think in terms of **request → governed execution → review → promotion → analytics**, the product will make sense quickly.
