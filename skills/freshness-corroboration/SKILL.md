---
name: freshness-corroboration
description: Audits content freshness, entity disambiguation, and web corroboration. Detects missing dates, ambiguous entity identity, and lack of third-party references.
license: MIT
allowed-tools:
  - web_fetch
  - web_search
  - file_read
  - file_write
---

# Freshness & Corroboration Audit Skill

## When to Use

Use when checking content freshness, entity clarity, and trust signals for AI citation.

## Inputs

- **url** (required): Website URL to audit

## Checks (by severity)

### HIGH Checks

**1. Ambiguous Entity Identity**
- Detection: Check for Wikipedia page, Wikidata entity, consistent NAP (Name/Address/Phone)
- Mechanism: AI cannot cite what it cannot identify. Ambiguous names get mixed up
- Fix: Add disambiguation signals, consistent NAP, Wikipedia/Wikidata entries
- Evidence: "Brand name 'Apple' ambiguous. No disambiguation signals found."

### MEDIUM Checks

**2. No Freshness Signals**
- Detection: Check for date meta tags, structured data dates, visible dates
- Mechanism: AI prioritizes fresh content. Without dates, content appears stale
- Fix: Add publication dates, dateModified in structured data
- Evidence: "No publication or modification dates found. Content appears stale."

**3. Conflicting Information**
- Detection: Crawl multiple pages, compare NAP consistency
- Mechanism: AI cannot determine which source is correct
- Fix: Ensure consistent NAP across all pages
- Evidence: "Found 3 different addresses across pages"

**4. No Corroboration (Single Source)**
- Detection: Search for brand mentions across web (requires web_search)
- Mechanism: AI treats multi-source facts as more trustworthy
- Fix: Get mentioned in news, blogs, Wikipedia
- Evidence: "Brand mentioned only on own site. No third-party references found."

### LOW Checks

**5. Missing Entity Disambiguation**
- Detection: Check for schema.org sameAs links, unique identifiers
- Mechanism: AI may confuse brand with competitors
- Fix: Add sameAs links to Wikipedia, social profiles
- Evidence: "No entity disambiguation signals found."

## Procedure

1. Validate the input URL.
2. Fetch the target page using an HTTP request.
3. Record the final URL, HTTP status code, response headers, and raw HTML.
4. Fetch and parse `/robots.txt`.
5. Run the critical crawlability checks:
   - Meta robots NOINDEX
   - X-Robots-Tag NOINDEX
   - robots.txt blocking
   - HTTP errors
6. Analyze the raw HTML for rendering signals:
   - Amount of visible text
   - SPA/root containers
   - Framework indicators
   - `<noscript>` fallback
7. Run rendering-dependent checks where required.
8. Analyze page-level accessibility signals such as canonical tags and page size.
9. Convert every detected problem into a structured finding containing:
   - check
   - severity
   - evidence
   - mechanism
   - suggested action
10. Return the findings as a JSON array.
11. Do not modify the website or perform authenticated/destructive actions.

## Output Format

Returns JSON array of findings with evidence, mechanism, and suggested action.

## Examples

**Example 1: Ambiguous identity**
```
Input: "https://newbrand.com"
Output: [{
  "check": "entity_identity",
  "found": true,
  "severity": "high",
  "evidence": "No Wikipedia page or Wikidata entity found. Brand name may be ambiguous.",
  "mechanism": "AI cannot identify which entity to cite without disambiguation signals",
  "suggested_action": {
    "summary": "Create Wikipedia page, add consistent NAP, build web presence",
    "priority": "high"
  }
}]
```

## Notes

- Focuses on Stage 5 (Retrieval) of AI crawl pipeline
- Requires web_search tool for corroboration checks
- Entity disambiguation is critical for unknown brands
