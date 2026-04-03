# Architecture and Design

## Architectural Model

RGP follows the layered model defined in the constitution:

- Experience Plane
- Governance Plane
- Coordination Plane
- Execution Plane
- Runtime Plane
- Observation and Intelligence Plane

The implementation maps those layers into a practical application stack.

## Major Runtime Components

### Web Application

- **Technology**: Next.js, React, TypeScript, Tailwind CSS
- **Role**: operational UI, analytics UI, admin authoring surfaces, request and session drill-down experiences

### API Application

- **Technology**: FastAPI, Pydantic, SQLAlchemy
- **Role**: authoritative request lifecycle, template governance, org model, integration model, analytics APIs, event recording, agent session APIs

### Worker / Async Execution

- **Technology**: Celery scaffold plus local async execution path
- **Role**: background checks and governed async execution

### Data and Eventing

- relational persistence for governed entities
- event ledger and outbox behavior
- performance metric persistence
- object store seam for artifacts and blob-oriented outputs

## Canonical Domain Model

The canonical root object is the **Request**. It links out to the other governed objects:

- Runs
- Checks
- Reviews
- Promotions
- Artifacts
- Conversations / Agent Sessions

This preserves the IA rule that the request is the primary entry point for governed work.

## Key Design Decisions

### Request as the System of Record

Execution systems may know runtime state, but RGP owns authoritative request state, approval state, artifact governance state, and promotion eligibility.

### Immutable Template Version Binding

Requests bind to a concrete template version at submission time. That prevents definition drift and preserves historical explainability.

### Table-First Information Architecture

The UI follows the repository IA and design rules:

- lists are the canonical entry point
- drill-down follows list → detail → sub-detail
- tables dominate operational views
- actions are contextual, not ambient

### Explicit State and Actions

The style guide forbids hidden state and silent behavior. That shows up in:

- explicit request statuses
- explicit review and promotion steps
- explicit agent-session acceptance to resume workflow
- explicit analytics filters and comparisons

## Agent Integration Model

RGP supports direct assignment of requests to external agents such as OpenAI Codex, Anthropic Claude Code, and Microsoft Copilot-style integrations.

Important design point:

- an agent assignment is not modeled as a single request/response call
- it is modeled as a persistent **agent session**
- the session maintains transcript, status, latest response, and resumption behavior

This design exists because real agent work is iterative and requires human follow-up and acceptance.

## Observability and Analytics Design

The platform records:

- API performance metrics
- event history
- workflow and agent analytics
- delivery lifecycle metrics
- cost and operational metrics
- portfolio, team, and user rollups

The intent is that metrics are derived from traceable underlying governed data, consistent with the constitutional requirement that metrics remain evidence-backed.

## Security Design Principles

The current implementation includes:

- explicit auth cookies and bearer-token paths for local/dev flows
- encrypted-at-rest integration secrets
- write-only secret handling in admin integration management
- outbound integration URL allowlists
- security scanning as part of the comprehensive test suite

## Repository Structure

The main repo layout is:

```text
apps/
  api/
  web/
  worker/
packages/
  api-client/
  config/
  domain/
  telemetry/
  ui/
docs/
infra/
scripts/
tests/
```

## Key Source References

- Architecture diagrams:
  - [`c4-1.puml`](https://github.com/pauljbernard/rgp/blob/main/c4-1.puml)
  - [`c4-depl.puml`](https://github.com/pauljbernard/rgp/blob/main/c4-depl.puml)
- Domain specification:
  - [`build_pack_1.md`](https://github.com/pauljbernard/rgp/blob/main/build_pack_1.md)
- IA:
  - [`ia.md`](https://github.com/pauljbernard/rgp/blob/main/ia.md)
- Design system and style:
  - [`design_system.md`](https://github.com/pauljbernard/rgp/blob/main/design_system.md)
  - [`style_guide.md`](https://github.com/pauljbernard/rgp/blob/main/style_guide.md)

## Design Summary

RGP is intentionally designed as:

- governance-first
- request-centered
- table-first in UX
- agent-capable
- analytics-backed
- constitution-driven

That is the architecture’s central idea: execution remains important, but governance owns the meaning of execution.
