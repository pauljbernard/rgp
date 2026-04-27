# Functional Tests

This directory contains in-process API contract tests that sit between isolated unit tests and live integration runs.

Primary goals:

- verify HTTP status mapping and error envelopes
- validate request/response contracts without a running local stack
- exercise route composition with mocked service dependencies

Run locally:

```bash
cd /Volumes/data/development/rgp
pnpm test:functional
```

These tests complement:

- `/Volumes/data/development/rgp/tests/unit`
- `/Volumes/data/development/rgp/tests/integration`
