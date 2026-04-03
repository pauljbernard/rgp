# Performance And Scalability Tests

This directory contains executable performance and scalability validation for the platform.

Primary suite:

- [/Volumes/data/development/rgp/tests/performance/test_performance_scalability.py](/Volumes/data/development/rgp/tests/performance/test_performance_scalability.py)
  - read-path concurrency validation
  - draft-creation write-path concurrency validation
  - performance analytics capture verification
  - JSON summary artifact generation

Run locally:

```bash
cd /Volumes/data/development/rgp
pnpm test:performance
```

Execution notes:

- the API must be running locally and reachable at `RGP_API_BASE` or `http://127.0.0.1:8001`
- development auth must remain enabled so the suite can mint a local bearer token
- the suite writes its summary artifact to:
  - [/Volumes/data/development/rgp/coverage/performance-summary.json](/Volumes/data/development/rgp/coverage/performance-summary.json)
