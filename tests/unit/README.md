# Unit Tests

This directory contains isolated unit coverage for backend services and other pure-logic seams that should not rely on browser or end-to-end execution.

Run locally:

```bash
cd /Volumes/data/development/rgp
pnpm test:api-unit
```

Current focus areas:

- agent provider selection, fallback, chunking, and request wiring
- event publishing logic
- object store persistence behavior
- check dispatch helper behavior
- performance analytics aggregation helpers

These tests complement:

- `/Volumes/data/development/rgp/tests/integration/test_end_to_end_user_stories.py`
- `/Volumes/data/development/rgp/apps/web/e2e/*.spec.ts`
