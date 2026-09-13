# Crawl and Render Severity Guidance

The audit agent uses this guidance when interpreting crawl and render
observations.

Severity is contextual and must not be assigned solely from the name
of a check.

Consider:

1. Whether the affected content is important.
2. Whether the problem blocks access or only reduces quality.
3. Whether supporting observations confirm the problem.
4. Whether the issue affects one page or many pages.
5. Whether the behavior may be intentional.
6. Confidence in the evidence.

---

## Critical

Use when strong evidence indicates that important public content is
directly prevented from being discovered or accessed.

Examples:

- an important public page has `noindex`
- an important page consistently returns a 5xx error
- a broad access rule prevents important public content from being
  fetched

Critical should be reserved for genuine showstopper or site-wide
problems.

---

## High

Use when the website is technically reachable but substantial important
content may be unavailable or difficult for automated retrieval.

Examples:

- important content is strongly dependent on client-side rendering and
  is absent from raw HTML
- raw HTML contains almost no meaningful content despite important
  page functionality
- relevant crawler access is restricted from important public content

Strong supporting evidence should exist before assigning high severity.

---

## Medium

Use for meaningful technical weaknesses that reduce reliability,
interpretability, discoverability, or rendering quality without directly
blocking access.

Examples:

- meaningful canonical ambiguity
- excessive page size or blocking resources with evidence of material
  impact
- missing fallback content when rendering dependency is established

Optional metadata or tags should not automatically receive medium
severity.

---

## Low

Use for minor optimization opportunities or weak signals with limited
impact.

Examples:

- performance improvements with limited demonstrated impact
- weak rendering signals where important content remains available
- small technical improvements that do not materially affect discovery

---

## Important False-Positive Rules

Do not assign severity merely because:

- JavaScript is present
- a framework is detected
- a canonical is absent
- a sitemap is absent
- a noscript tag is absent
- lazy loading is used
- robots.txt contains any restriction
- a local tool experienced TLS, DNS, proxy, or connection problems

These observations require context before becoming findings.