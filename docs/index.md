---
title: Request Governance Platform Docs
section: Documentation Home
summary: A formal documentation site for product guidance, architecture, implementation reporting, and API contracts published from the repository docs directory.
source_path: docs/index.md
---

<section class="hero-grid">
  <div class="hero-panel">
    <div class="eyebrow">Governance-First Control Plane</div>
    <h2>Documentation organized for product users, engineers, and implementation reviewers.</h2>
    <p>
      This GitHub Pages site turns the repository documentation into a structured reference experience:
      product guidance, architecture rationale, implementation reports, and API contracts now live behind
      stable URLs with coherent navigation.
    </p>
    <div class="hero-actions">
      <a class="primary-button" href="{{ '/wiki/' | relative_url }}">Enter The Wiki</a>
      <a class="secondary-button" href="{{ '/implementation/' | relative_url }}">Implementation Overview</a>
      <a class="secondary-button" href="{{ '/reports/traceability-matrix/' | relative_url }}">Traceability Matrix</a>
    </div>
  </div>

  <aside class="spotlight-panel">
    <h2>At A Glance</h2>
    <p>Start with the reading path that matches your job to be done.</p>
    <div class="metric-stack">
      <div class="metric-tile">
        <div class="metric-label">For New Users</div>
        <div class="metric-value">Quick Start</div>
      </div>
      <div class="metric-tile">
        <div class="metric-label">For Engineers</div>
        <div class="metric-value">Developer Guide</div>
      </div>
      <div class="metric-tile">
        <div class="metric-label">For Reviewers</div>
        <div class="metric-value">Traceability + Gap Analysis</div>
      </div>
    </div>
  </aside>
</section>

<section class="section-heading">
  <h2>Core Paths</h2>
  <p>Each section below is now published as a navigable page set rather than a loose collection of Markdown files.</p>
</section>

<section class="card-grid">
  <article class="doc-tile">
    <div class="kicker">Wiki</div>
    <h3>Product and engineering guidance</h3>
    <p>Canonical reading path for platform rationale, architecture, standards, developer setup, and end-user guidance.</p>
    <a href="{{ '/wiki/' | relative_url }}">Open wiki home</a>
  </article>
  <article class="doc-tile">
    <div class="kicker">Implementation</div>
    <h3>Execution-facing documentation</h3>
    <p>Start here if you need the implementation-facing overview of what the codebase currently documents.</p>
    <a href="{{ '/implementation/' | relative_url }}">Open implementation overview</a>
  </article>
  <article class="doc-tile">
    <div class="kicker">Reports</div>
    <h3>Formal status and remediation documents</h3>
    <p>Gap analysis, phase tracking, and traceability reporting for ongoing platform delivery and review.</p>
    <a href="{{ '/reports/gap-analysis/' | relative_url }}">Open reports</a>
  </article>
  <article class="doc-tile">
    <div class="kicker">API</div>
    <h3>Integration contracts</h3>
    <p>Shared external contract documentation for systems that integrate with RGP governance flows.</p>
    <a href="{{ '/api/flightos-instructional-governance/' | relative_url }}">Open API contract</a>
  </article>
</section>

<section class="section-heading">
  <h2>Recommended Reading Order</h2>
  <p>This sequence works well for someone new to the platform who needs both context and operational understanding.</p>
</section>

<section class="card-grid">
  <article class="doc-tile">
    <div class="kicker">1</div>
    <h3>Constitution and Requirements Rationale</h3>
    <p>Understand why the platform exists and what governance posture it enforces.</p>
    <a href="{{ '/wiki/constitution-requirements-rationale/' | relative_url }}">Read the rationale</a>
  </article>
  <article class="doc-tile">
    <div class="kicker">2</div>
    <h3>Architecture and Design</h3>
    <p>See the runtime model, major components, and the request-centered domain shape.</p>
    <a href="{{ '/wiki/architecture/' | relative_url }}">Read the architecture guide</a>
  </article>
  <article class="doc-tile">
    <div class="kicker">3</div>
    <h3>Quick Start and In-Depth Guides</h3>
    <p>Move from orientation to actual product usage through the user-facing documentation.</p>
    <a href="{{ '/wiki/quick-start/' | relative_url }}">Open the user guides</a>
  </article>
  <article class="doc-tile">
    <div class="kicker">4</div>
    <h3>Developer Guide and Standards</h3>
    <p>Set up the repo, understand runtime expectations, and follow the project engineering rules.</p>
    <a href="{{ '/wiki/developer-guide/' | relative_url }}">Open the engineering docs</a>
  </article>
</section>

<div class="callout">
  Some implementation-analysis documents were generated from local repository reviews and may reference code paths directly.
  They are preserved as formal published artifacts here, but the primary navigation entry points are the curated pages above.
</div>
