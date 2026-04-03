# Integration Tests

This directory contains executable API and workflow integration coverage for the platform.

Primary suites:

- `/Volumes/data/development/rgp/tests/integration/test_end_to_end_user_stories.py`
  - constitution- and requirements-derived end-to-end user stories
  - targets the live local API at `http://127.0.0.1:8001` by default
  - issues a dev bearer token at runtime through `/api/v1/auth/dev-token`

- `/Volumes/data/development/rgp/tests/performance/test_performance_scalability.py`
  - concurrency-based performance and scalability validation
  - validates read-path and write-path thresholds
  - confirms performance analytics capture

Run locally:

```bash
cd /Volumes/data/development/rgp
pnpm test:integration
pnpm test:performance
```

Execution notes:

- the API must be running locally and reachable at `RGP_API_BASE` or `http://127.0.0.1:8001`
- development auth must remain enabled so the suite can mint a local bearer token
- the suite validates live workflow behavior, not only isolated repository code paths
