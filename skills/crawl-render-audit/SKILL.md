---
name: crawl-render-audit
description: Audits crawlability, rendering, and accessibility for AI crawlers. Detects NOINDEX, robots.txt blocks, HTTP errors, empty HTML, and missing noscript fallbacks.
license: MIT
allowed-tools:
  - web_fetch
  - file_read
  - file_write
---

# Crawl & Render Audit Skill

## When to Use

Use when checking if AI crawlers can access and read a website.

## Inputs

- **url** (required): Website URL to audit

## Checks (by severity)

### CRITICAL Checks

**1. Meta Robots NOINDEX**
- Detection: Check meta[name='robots'] for 'noindex' in content
- Also check X-Robots-Tag header
- Mechanism: Hard block prevents indexing. AI cannot cite content it cannot index.
- Fix: Remove noindex or change to 'index, follow'

**2. robots.txt Blocking**
- Detection: Parse /robots.txt for 'Disallow: /' without 'Allow: /' override
- Mechanism: AI respects robots.txt. Blanket blocking makes site invisible.
- Fix: Add 'Allow: /' or remove blanket Disallow

**3. HTTP Errors**
- Detection: Check HTTP status code (4xx/5xx = critical, timeout = high)
- Mechanism: Broken pages cannot be fetched
- Fix: Fix server errors, improve performance

### HIGH Checks

**4. Empty HTML / JS-Only Rendering**
- Detection: Check if HTML text content <200 chars
- Mechanism: SPAs render client-side. AI sees blank page.
- Fix: Implement SSR/SSG or add noscript fallback

**5. Missing noscript Fallback**
- Detection: Check for <noscript> tags when SPA detected
- Mechanism: AI crawlers often don't execute JS
- Fix: Add noscript content for critical info

**6. SPA Framework Detection**
- Detection: Check for root divs (id="root", id="app"), framework scripts
- Mechanism: Content in JS bundle, not HTML
- Fix: SSR/SSG, noscript fallback

### MEDIUM Checks

**7. Missing Canonical Tag**
- Detection: Check for <link rel='canonical'>
- Mechanism: Without canonical, AI may cite wrong URL
- Fix: Add self-referencing canonical

**8. Performance Signals**
- Detection: Page size >500KB (high), >200KB (medium); >5 render-blocking scripts
- Mechanism: Large pages may timeout crawlers
- Fix: Reduce page size, add async/defer to scripts

## Output Format

Returns JSON array of findings:

```json
[
  {
    "check": "noindex_detection",
    "found": true,
    "severity": "critical",
    "evidence": "Found <meta name=\"robots\" content=\"noindex\">",
    "mechanism": "NOINDEX prevents indexing",
    "suggested_action": {
      "summary": "Remove noindex or change to 'index, follow'",
      "priority": "critical"
    }
  }
]
```

## Examples

**Example 1: NOINDEX detected**
```
Input: "https://microsoft.com"
Output: [{
  "check": "noindex_detection",
  "found": true,
  "severity": "critical",
  "evidence": "Found <meta name=\"robots\" content=\"noindex\">"
}]
```

**Example 2: Clean site**
```
Input: "https://example.com"
Output: []
```

## Notes

- Focuses on Stages 1-2 of AI crawl pipeline (Discovery & Fetching)
- All findings include evidence, mechanism, and fix
- Respects robots.txt
