---
name: engagement-audit
description: Audits on-site engagement signals and content accessibility. Detects hidden content, poor alt text, weak semantic HTML, and unclear above-fold content.
license: MIT
allowed-tools:
  - web_fetch
  - file_read
  - file_write
---

# Engagement Audit Skill

## When to Use

Use when checking on-site engagement signals and content accessibility for both users and AI crawlers.

## Inputs

- **url** (required): Website URL to audit

## Checks (by severity)

### MEDIUM Checks

**1. Hidden Content Patterns**
- Detection: Check for display:none, visibility:hidden, aria-hidden, tabs/accordions
- Mechanism: Content hidden from initial crawl. AI sees only visible content
- Fix: Progressive disclosure - content in HTML, hidden with CSS
- Evidence: "Found 3 instances of display:none hiding important content"

**2. Low Image Alt Text Coverage**
- Detection: Count images with/without alt attributes, calculate percentage
- Mechanism: AI cannot see images without alt text. Visual content is dark matter
- Fix: Add descriptive alt text to all images (target: >80% coverage)
- Evidence: "Only 17% of images have alt text. 80 of 97 images are invisible to AI."

**3. Lazy Loading Without Fallback**
- Detection: Check for loading="lazy", data-lazy, IntersectionObserver
- Mechanism: AI doesn't scroll. Lazy-loaded content invisible without interaction
- Fix: Add noscript fallback or inline critical images
- Evidence: "27 lazy-loaded images without noscript fallback"

**4. Content in iframes**
- Detection: Count iframes, check for important content inside
- Mechanism: iframes treated as separate pages by crawlers
- Fix: Inline critical content or ensure iframe is crawlable
- Evidence: "Found 5 iframes with potentially important content"

### LOW Checks

**5. Minimal Semantic HTML**
- Detection: Count semantic tags (header, nav, main, article, section, footer)
- Mechanism: Semantic HTML provides content context to AI
- Fix: Use semantic HTML5 elements instead of generic divs
- Evidence: "Only 2 semantic HTML tags found. Consider using <main>, <article>, <section>."

**6. Poor Internal Linking**
- Detection: Count internal vs external links, check for orphan pages
- Mechanism: AI discovers pages by following links. Orphan pages are never found
- Fix: Add internal links from relevant pages
- Evidence: "Found 15 orphan pages with no internal links"

**7. Unclear Above-Fold Content**
- Detection: Analyze visible content in first viewport (first ~600px)
- Mechanism: AI extracts what's immediately visible
- Fix: Clear headline and value proposition above fold
- Evidence: "Primary message not visible without scrolling"

**8. Poor Mobile Signals**
- Detection: Check viewport meta tag, test responsive breakpoints
- Mechanism: Mobile-first indexing. Poor mobile hurts rankings
- Fix: Add viewport meta tag, implement responsive design
- Evidence: "Missing viewport meta tag. Not optimized for mobile."

## Output Format

Returns JSON array of findings with evidence, mechanism, and suggested action.

## Examples

**Example 1: Hidden content**
```
Input: "https://example.com"
Output: [{
  "check": "hidden_content",
  "found": true,
  "severity": "medium",
  "evidence": "Found important content hidden with display:none in tabs",
  "mechanism": "AI sees only visible content during initial crawl",
  "suggested_action": {
    "summary": "Use progressive disclosure: content in HTML, hidden with CSS",
    "priority": "medium"
  }
}]
```

## Notes

- Focuses on Stage 3 (Parsing) and Stage 4 (Extraction) of AI crawl pipeline
- Balances AI discoverability with user engagement
- Hidden content hurts both AI and users (accessibility)
