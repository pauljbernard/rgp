# Request Governance Platform

This repository is the implementation scaffold for the Request Governance Platform (RGP).

The original source specifications currently live in the repository root:

- `constitution.md`
- `requirements.md`
- `ia.md`
- `design_system.md`
- `style_guide.md`
- `build_pack_1.md`
- `build_pack_2.md`
- `build_pack_3.md`
- `c4-1.pml`
- `c4-depl.pml`

## Stack

- Web: Next.js, React, TypeScript, Tailwind CSS
- API: FastAPI, Pydantic
- Worker: Celery scaffold
- Data: PostgreSQL, Redis, DynamoDB Local (migration target)

## Repository Layout

```text
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
infra/
scripts/
tests/
```

## Quick Start

1. Install Node dependencies:

```bash
pnpm install
```

2. Create a Python virtual environment and install API and worker dependencies:

```bash
cd apps/api && python3 -m venv .venv && source .venv/bin/activate && pip install -e .
cd ../worker && python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

3. Start the API:

```bash
cd apps/api && source .venv/bin/activate && uvicorn app.transport:get_asgi_app --factory --reload --port 8000
```

4. Start the web app:

```bash
pnpm --filter @rgp/web dev
```

5. Optionally run local infrastructure:

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

## DynamoDB Migration Slice

The first active DynamoDB migration slice is template persistence.

Local development defaults remain SQL-backed. To exercise the template slice against DynamoDB Local:

```bash
cd apps/api
export PYTHONPATH=.
export RGP_DYNAMODB_ENDPOINT_URL=http://localhost:8000
export RGP_TEMPLATE_PERSISTENCE_BACKEND=dynamodb
python -m app.persistence.dynamodb_bootstrap
python ../../scripts/verify-template-dynamodb-parity.py
```

That path:
- ensures the `rgp-governance` table exists
- seeds the template slice into DynamoDB
- compares template operations across SQL and DynamoDB adapters

## Current Scope

This scaffold includes:

- a Requests list screen
- an in-memory request repository for local development
- initial `/api/v1/requests` and `/api/v1/templates` endpoints
- shared TypeScript contracts for the web layer

It does not yet include persistent storage, auth, event streaming, or generated API clients.

## License

This repository uses a split licensing model.

- Software and source code are licensed under PolyForm Noncommercial 1.0.0.
- Documentation, specifications, diagrams, and other non-software content are licensed under
  Creative Commons Attribution-NonCommercial 4.0 International (`CC BY-NC 4.0`).

Commercial use is not permitted under the public repository licenses.

This is a noncommercial source-available posture, not an OSI-approved open-source software
license. See [LICENSE.md](./LICENSE.md).

## Contributions And Commercial Rights

Outside contributions are accepted only under the repository's contributor policy and CLA:

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CLA.md](./CLA.md)

In substance:

- all commercial-use rights are reserved under the public repository licenses
- commercial exceptions are granted only by Paul Bernard or his authorized designee
- contributions are accepted only under terms that preserve Paul Bernard's right to offer separate commercial licenses and other commercial exceptions in the future
