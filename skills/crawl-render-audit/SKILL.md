
```markdown
---
name: crawl-render-audit
description: Audits crawlability, rendering, and accessibility for AI crawlers. Detects HTTP access problems, robots restrictions, indexing directives, empty or JavaScript-dependent HTML, and important rendering barriers.
license: MIT
allowed-tools:
  - web_fetch
  - file_read
  - file_write
---

# Crawl & Render Audit Skill

## When to Use

Use when checking whether AI crawlers can access and read a website.

## Inputs

- **url** (required): Website URL to audit

## Reasoning Rules

- A failed fetch should be reported as an access problem only when supported by evidence.
- Do not treat a local TLS, proxy, DNS, or tool failure as proof that the website blocks AI crawlers.
- Targeted robots.txt restrictions are not the same as a site-wide block.
- Missing canonical, sitemap, or noscript tags are not automatically defects.
- JavaScript usage alone is not a problem. Flag it when important content is unavailable or substantially reduced without rendering.
- Lazy loading alone is not a finding unless important content becomes inaccessible.
- If a check cannot be reliably evaluated, return `unverified`.

## Checks

### 1. Meta Robots NOINDEX

- Detection: Check `meta[name="robots"]` and relevant page-level robots directives for `noindex`.
- Also check the `X-Robots-Tag` response header when available.
- Mechanism: A noindex directive can prevent a page from being indexed or surfaced through search and discovery systems.
- Fix: Review the intended indexing policy and remove or change the directive when public discovery is desired.

### 2. robots.txt Blocking

- Detection: Parse `/robots.txt` and determine whether relevant crawlers are broadly prevented from accessing important public content.
- A targeted restriction on a specific path or crawler is not equivalent to a site-wide block.
- Mechanism: Broad crawler restrictions can reduce AI discoverability.
- Fix: Review the intended crawler policy and allow appropriate public content where discovery is desired.

### 3. HTTP Errors

- Detection: Check HTTP status codes, redirects, timeouts, and connection failures.
- 4xx/5xx responses may indicate an access problem when they affect important public pages.
- Mechanism: Inaccessible pages cannot be reliably fetched or cited.
- Fix: Resolve confirmed server or access problems.
- Do not report an environment-specific network or certificate failure as a website defect without supporting evidence.

### 4. Empty HTML / JS-Dependent Rendering

- Detection: Check whether important page content is absent from server-readable HTML or whether the page is substantially empty without client-side rendering.
- Mechanism: Content that depends entirely on client-side execution may be less accessible to systems that cannot render the page.
- Fix: Use server-side rendering, static generation, or another reliable fallback for important content.

### 5. Missing Rendering Fallback

- Detection: Check for `<noscript>` or equivalent server-rendered fallback only when important content depends on client-side rendering.
- Do not report missing `<noscript>` when important content is already present in server-readable HTML.
- Mechanism: Important content unavailable without rendering may reduce machine accessibility.
- Fix: Ensure important content remains available through server-rendered HTML or an appropriate fallback.

### 6. SPA / Framework Rendering Signals

- Detection: Look for root containers, framework indicators, and other signals of client-side application rendering.
- JavaScript framework usage alone is not a defect.
- Flag only when rendering signals are combined with evidence that important content is not available in readable HTML.

### 7. Canonical Signals

- Detection: Check for canonical URL signals and consistency with the page URL.
- Mechanism: Missing or inconsistent canonical signals can make duplicate-page and URL interpretation less clear.
- Do not treat a missing canonical as a major discoverability failure by itself.
- Fix: Add or correct canonical signals when duplicate or URL ambiguity is a meaningful concern.

### 8. Performance Signals

- Detection: Check available page-size and script-loading signals.
- Large pages or excessive blocking resources may create practical crawl or loading problems.
- Do not treat a page-size threshold as a guaranteed crawler failure.
- Use the evidence and context to determine whether the issue is material.

### 9. Internal Link Discovery

- Detection: Identify important internal links from the audited page where possible.
- Consider whether important sections are discoverable through normal site navigation or internal links.
- Do not claim that pages are orphaned unless multiple pages have actually been inspected.

## Output

Return structured observations that distinguish:

```json
{
  "check": "CR-001",
  "status": "issue",
  "evidence": "Evidence supporting the issue.",
  "details": {
    "impact": "major",
    "scope": "sitewide"
  }
}
