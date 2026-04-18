---
title: Coding and Testing Standards
permalink: /wiki/coding-testing-standards/
section: Wiki
summary: Engineering standards for specification-driven implementation, layer discipline, and the required testing strands.
source_path: docs/wiki/Coding-and-Testing-Standards.md
---

# Coding and Testing Standards

## Coding Standards

The codebase follows a few simple but strict principles.

### 1. Specification-Driven Implementation

Core behavior must align with:

- the constitution
- the requirements
- the build packs
- the IA and design guides

If implementation and spec diverge, the spec is the first place to check and then update deliberately if needed.

### 2. Canonical Terminology

Use the platform’s canonical vocabulary consistently:

- Request
- Run
- Artifact
- Review
- Approval
- Promotion

Do not invent local synonyms for core domain objects.

### 3. Explicitness Over Cleverness

The repo prefers:

- explicit state transitions
- explicit validation
- explicit error handling
- explicit routing and governance logic

Hidden behavior and “magic” are considered defects in this system.

### 4. Layer Discipline

Keep responsibilities separated:

- web for interaction and presentation
- API for authoritative platform behavior
- services for business logic seams
- repositories for persistence concerns
- packages for shared contracts and components

## Testing Standards

RGP treats testing as a first-class product requirement.

### Required Test Strands

The comprehensive suite includes:

- **unit tests**
  - backend services
  - shared UI components
  - web route and page logic
- **integration tests**
  - constitution- and requirements-derived user stories
- **browser journey tests**
  - high-value UI paths
- **security scanning**
  - static security review
  - dependency audit
  - crypto review
- **performance and scalability tests**
  - read/write concurrency
  - threshold validation
  - performance analytics capture

### Coverage Standard

The current target is **at least 85% unit coverage across all tracked dimensions**:

- API unit coverage
- web unit/route coverage
- UI package unit coverage
- combined repo unit coverage

Coverage is measured, not estimated.

### Test Entry Points

From the repo root:

```bash
pnpm test:unit
pnpm test:integration
pnpm test:journey
pnpm test:security
pnpm test:performance
pnpm test:comprehensive
```

### User Story Validation

The end-to-end suite is organized around named user stories, documented in:

- [`tests/e2e/USER_STORIES.md`](https://github.com/pauljbernard/rgp/blob/main/tests/e2e/USER_STORIES.md)

That matters because the platform is validated against the constitution and requirements, not just isolated code paths.

### Security Standard

A full comprehensive test run must include:

- Bandit/static security scan
- Python dependency vulnerability audit
- JavaScript dependency vulnerability audit
- crypto review

Security is therefore part of release validation, not a separate optional exercise.

### Performance Standard

A full comprehensive run also includes:

- concurrent read-path validation
- concurrent write-path validation
- latency and throughput threshold checks
- verification that performance analytics capture the exercised workload

## Pull Request / Change Expectations

Any meaningful change should include:

- clear problem statement
- code changes aligned to the domain model
- test updates where behavior changed
- no regression against the comprehensive suite

## Standards Summary

RGP favors:

- explicit governed behavior
- constitution-aligned implementation
- measurable quality
- evidence-backed security and performance validation

That is how the project keeps the platform coherent as it grows.
