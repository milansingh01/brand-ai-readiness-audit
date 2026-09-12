---
name: structured-data-audit
description: Audits structured data, meta tags, and machine-readable content. Detects missing JSON-LD, Open Graph, Twitter Cards, meta descriptions, and heading hierarchy issues.
license: MIT
allowed-tools:
  - web_fetch
  - file_read
  - file_write
---

# Structured Data Audit Skill

## When to Use

Use when checking if website content is machine-readable and properly structured for AI extraction.

## Inputs

- **url** (required): Website URL to audit

## Checks (by severity)

### HIGH Checks

**1. No JSON-LD Structured Data**
- Detection: Check for `<script type="application/ld+json">`
- Mechanism: Without structured data, AI must infer from plain text (error-prone)
- Fix: Add JSON-LD for Organization, Product, Article schemas
- Evidence: "No JSON-LD found. AI cannot extract entity information."

**2. Poor Heading Hierarchy**
- Detection: Check H1 count (should be exactly 1), verify no skipped levels
- Mechanism: H1 signals primary topic. Multiple H1s or missing H1 confuses AI
- Fix: Ensure 1 H1 per page, logical H2-H3 progression

### MEDIUM Checks

**3. No Meta Description**
- Detection: Check for `<meta name="description">`
- Mechanism: Meta description provides controlled summary. Without it, AI extracts random text
- Fix: Add concise (150-160 chars), descriptive meta description

**4. Invalid JSON-LD**
- Detection: Validate JSON syntax, check required fields for schema type
- Mechanism: Invalid schema is ignored by AI
- Fix: Validate against schema.org, include all required fields

**5. Missing Open Graph Tags**
- Detection: Check for og:title, og:description, og:image, og:url
- Mechanism: OG tags provide social sharing context and additional signals
- Fix: Add Open Graph meta tags

### LOW Checks

**6. Missing Twitter Cards**
- Detection: Check for twitter:card, twitter:title, twitter:description
- Mechanism: Bonus signals for content context
- Fix: Add Twitter Card meta tags

**7. Low Image Alt Text Coverage**
- Detection: Count images with/without alt attributes
- Mechanism: AI cannot see images without alt text
- Fix: Add descriptive alt text to all images

**8. Minimal Semantic HTML**
- Detection: Count semantic tags (header, nav, main, article, section, footer)
- Mechanism: Semantic HTML provides content context
- Fix: Use semantic HTML5 elements

## Output Format

Returns JSON array of findings with same format as crawl-render-audit.

## Examples

**Example 1: No JSON-LD**
```
Input: "https://example.com"
Output: [{
  "check": "structured_data",
  "found": true,
  "severity": "high",
  "evidence": "No JSON-LD structured data found on homepage",
  "mechanism": "AI must infer entity info from plain text, leading to errors",
  "suggested_action": {
    "summary": "Add JSON-LD Organization schema to homepage",
    "priority": "high"
  }
}]
```

## Notes

- Focuses on Stage 4 (Extraction) of AI crawl pipeline
- Structured data is a force multiplier for unknown brands
- Famous brands can succeed without it, but unknown brands need it
