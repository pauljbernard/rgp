---
title: Wiki Home
permalink: /wiki/
section: Wiki
summary: Entry page for the first-version RGP documentation set, including rationale, architecture, engineering guidance, and user documentation.
source_path: docs/wiki/Home.md
---

# Request Governance Platform Wiki

Welcome to the first-version documentation for the Request Governance Platform (RGP).

RGP is a governance-first control plane for work. It treats a **request** as the authoritative unit of governed execution, supports both human and agent collaboration, and keeps ownership, review, approval, promotion, analytics, and auditability under one model.

This wiki is organized around the major documentation strands for the first release:

- [Constitution and Requirements Rationale]({{ '/wiki/constitution-requirements-rationale/' | relative_url }})
- [Architecture and Design]({{ '/wiki/architecture/' | relative_url }})
- [Coding and Testing Standards]({{ '/wiki/coding-testing-standards/' | relative_url }})
- [Developer Guide]({{ '/wiki/developer-guide/' | relative_url }})
- [Quick Start User Guide]({{ '/wiki/quick-start/' | relative_url }})
- [In-Depth User Guide]({{ '/wiki/in-depth-user-guide/' | relative_url }})

## Core Sources

The implementation and specification sources for this wiki live in the repository:

- Constitution: [`constitution.md`](https://github.com/pauljbernard/rgp/blob/main/constitution.md)
- Requirements: [`requirements.md`](https://github.com/pauljbernard/rgp/blob/main/requirements.md)
- Domain build pack: [`build_pack_1.md`](https://github.com/pauljbernard/rgp/blob/main/build_pack_1.md)
- Architecture diagrams: [`c4-1.puml`](https://github.com/pauljbernard/rgp/blob/main/c4-1.puml), [`c4-depl.puml`](https://github.com/pauljbernard/rgp/blob/main/c4-depl.puml)
- IA and design rules: [`ia.md`](https://github.com/pauljbernard/rgp/blob/main/ia.md), [`design_system.md`](https://github.com/pauljbernard/rgp/blob/main/design_system.md), [`style_guide.md`](https://github.com/pauljbernard/rgp/blob/main/style_guide.md)

## What This Release Includes

The current release includes:

- governed request lifecycle management
- template authoring and version governance
- organizations, teams, memberships, and portfolios
- direct agent assignment with persistent interactive sessions
- reviews, approvals, promotions, and deployments
- workflow, delivery, performance, cost, and portfolio analytics
- unit, integration, browser-journey, security, and performance test suites

## Recommended Reading Order

If you are new to the platform, read in this order:

1. [Constitution and Requirements Rationale]({{ '/wiki/constitution-requirements-rationale/' | relative_url }})
2. [Architecture and Design]({{ '/wiki/architecture/' | relative_url }})
3. [Quick Start User Guide]({{ '/wiki/quick-start/' | relative_url }})
4. [In-Depth User Guide]({{ '/wiki/in-depth-user-guide/' | relative_url }})
5. [Developer Guide]({{ '/wiki/developer-guide/' | relative_url }})
6. [Coding and Testing Standards]({{ '/wiki/coding-testing-standards/' | relative_url }})
