---
title: Wiki Source Notes
permalink: /wiki/source-notes/
section: Wiki
summary: Source-oriented note describing the mirrored wiki files that now power the published documentation site.
source_path: docs/wiki/README.md
---

# Wiki Mirror

This directory mirrors the GitHub wiki content for the Request Governance Platform.

The intended publication targets are:

- `https://github.com/pauljbernard/rgp/wiki`
- `https://pauljbernard.github.io/rgp/` when GitHub Pages is enabled from `/docs`

The following pages are maintained here so the documentation remains versioned in the main repository even if the GitHub wiki backend is not yet materialized:

- [Wiki Home]({{ '/wiki/' | relative_url }})
- [Constitution and Requirements Rationale]({{ '/wiki/constitution-requirements-rationale/' | relative_url }})
- [Architecture and Design]({{ '/wiki/architecture/' | relative_url }})
- [Coding and Testing Standards]({{ '/wiki/coding-testing-standards/' | relative_url }})
- [Developer Guide]({{ '/wiki/developer-guide/' | relative_url }})
- [Quick Start User Guide]({{ '/wiki/quick-start/' | relative_url }})
- [In-Depth User Guide]({{ '/wiki/in-depth-user-guide/' | relative_url }})
- `_Sidebar.md`

Once the GitHub wiki remote becomes available, these files can be pushed into `rgp.wiki.git`.
