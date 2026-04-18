---
title: Developer Guide
permalink: /wiki/developer-guide/
section: Wiki
summary: Repository setup, runtime workflow, and local environment guidance for contributors and maintainers.
source_path: docs/wiki/Developer-Guide.md
---

# Developer Guide

## Prerequisites

You will need:

- Node.js and `pnpm`
- Python 3.11+
- a local virtual environment for the API and worker
- optional Docker support for local infrastructure

## Repository Layout

```text
apps/
  api/       FastAPI application
  web/       Next.js application
  worker/    worker scaffold
packages/
  api-client/
  config/
  domain/
  telemetry/
  ui/
tests/
scripts/
infra/
```

## Local Setup

Install JavaScript dependencies:

```bash
cd /path/to/rgp
pnpm install
```

Create Python environments and install dependencies:

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

cd ../worker
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running the System

Start the API:

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.transport:get_asgi_app --factory --port 8001
```

Start the web app:

```bash
cd /path/to/rgp
pnpm --filter @rgp/web build
pnpm --filter @rgp/web start
```

For development mode:

```bash
pnpm --filter @rgp/web dev
```

## Environment and Credentials

Important local configuration points include:

- API base URL
- dev-auth settings
- integration provider settings
- encryption settings for integration secrets
- allowlists for outbound provider/runtime endpoints

Agent provider settings can now be managed in the application through **Admin → Integrations**, not only through environment variables.

## Key Developer Workflows

### Adding a New Domain Feature

1. check constitution and requirements first
2. update build pack or spec if the object model changes
3. implement API/domain behavior
4. wire web surfaces using the table-first IA
5. add or extend tests across the right layers

### Working on Templates

Use the template workbench:

- catalog at `/admin/templates`
- version drill-down for definition authoring
- publish only after validation passes

### Working on Request Journeys

The canonical flow is:

- create request
- submit
- assign to human and/or agent work
- validate/check
- review
- approve
- promote
- complete

### Working on Analytics

Analytics are not supposed to be disconnected dashboards. New metrics should remain traceable to:

- requests
- runs
- check runs
- reviews
- promotions
- performance records

## Test Workflow

Run targeted suites while developing:

```bash
pnpm test:unit
pnpm test:web
pnpm test:integration
pnpm test:journey
pnpm test:security
pnpm test:performance
```

Before a release-quality checkpoint:

```bash
pnpm test:comprehensive
```

## Important Source Files

- Constitution: [`constitution.md`](https://github.com/pauljbernard/rgp/blob/main/constitution.md)
- Requirements: [`requirements.md`](https://github.com/pauljbernard/rgp/blob/main/requirements.md)
- Domain build pack: [`build_pack_1.md`](https://github.com/pauljbernard/rgp/blob/main/build_pack_1.md)
- User stories: [`tests/e2e/USER_STORIES.md`](https://github.com/pauljbernard/rgp/blob/main/tests/e2e/USER_STORIES.md)

## Development Guidance

- treat the request as the primary root object
- preserve immutable template version semantics
- keep UX deterministic and table-first
- prefer drill-down over overloaded top-level pages
- do not introduce metrics that cannot be traced to governed data

## Developer Summary

The fastest way to work productively in this codebase is:

- start from the spec
- change the smallest coherent layer set
- validate with the right test strands
- keep governance authority separate from execution mechanics
