---
name: audit-orchestrator
description: Orchestrates all audit skills and produces the final audit report. Use when given a website URL to audit for AI discoverability and engagement issues.
license: MIT
allowed-tools:
  - web_fetch
  - file_read
  - file_write
---

# Audit Orchestrator Skill

## When to Use

Use this skill when:
- Given a website URL to audit
- Need to produce a comprehensive AI discoverability report
- Must coordinate multiple audit checks into a single output

## Inputs

- **url** (required): The website URL to audit (e.g., "https://example.com")
- **output_format** (optional): "json" (default) or "markdown"

## Procedure

### Step 1: Initialize Audit

1. Validate the URL format
2. Record audit timestamp in ISO 8601 format
3. Initialize findings list

### Step 2: Invoke Sub-Skills

Run each sub-skill in the marketplace and collect findings:

#### 2.1 Run crawl-render-audit
```
Skill: crawl-render-audit
Input: url
Expected Output: List of findings about crawlability, rendering, HTTP status
Severity: Critical (NOINDEX, robots.txt, HTTP errors) and High (JS rendering, empty HTML)
```

#### 2.2 Run structured-data-audit
```
Skill: structured-data-audit
Input: url
Expected Output: List of findings about structured data, meta tags, headings
Severity: Medium (missing JSON-LD, meta description) and High (poor headings)
```

#### 2.3 Run freshness-corroboration
```
Skill: freshness-corroboration
Input: url
Expected Output: List of findings about dates, entity disambiguation
Severity: Medium (no freshness signals) and High (ambiguous identity)
```

#### 2.4 Run engagement-audit
```
Skill: engagement-audit
Input: url
Expected Output: List of findings about engagement signals, accessibility
Severity: Medium (hidden content, alt text) and Low (mobile issues)
```

### Step 3: Merge and Deduplicate

1. Combine all findings from sub-skills
2. Remove duplicates (same issue reported by multiple skills)
3. Assign unique IDs: F-001, F-002, F-003, etc.

### Step 4: Prioritize Findings

Prioritize findings using severity, impact, scope, evidence confidence, and
the importance of the affected user/discovery journey.

Use severity as an important signal, but do not treat severity and priority
as identical.

Order the final findings primarily by recommended priority:

1. **HIGH PRIORITY** — Major impact on AI discoverability or a core visitor
   journey; broad or important scope; strong evidence; should be addressed soon.

2. **MEDIUM PRIORITY** — Meaningful impact, but limited scope or moderate
   effect on an important area; should be addressed after higher-impact issues.

3. **LOW PRIORITY** — Minor impact, limited scope, or an optimization that
   does not materially block discovery or engagement.

Severity should be assigned separately:

1. **CRITICAL** — Site-wide or showstopper problem; severely prevents AI
   discoverability or a core visitor journey.

2. **HIGH** — Major problem affecting an important discovery or engagement path.

3. **MEDIUM** — Significant but scoped problem with meaningful impact.

4. **LOW** — Minor issue or optimization with limited impact.

Do not assign severity or priority solely from the check name or observation.
Consider the website's context, scope, impact, evidence confidence, and whether
the behavior may be intentional.

If evidence is insufficient, mark the check as unverified rather than creating
a low-confidence finding.

Within the same priority level, order findings by severity and then by impact.

### Step 5: Generate Summary

Count findings by severity:
```json
{
  "total_findings": 10,
  "critical": 2,
  "high": 3,
  "medium": 4,
  "low": 1
}
```

### Step 6: Add Proactive Suggestions

Beyond fixing detected problems, suggest proactive improvements:
- Add JSON-LD structured data (even if not broken)
- Create Wikipedia/Wikidata entry (if missing)
- Build content strategy for corroboration
- Optimize for featured snippets

### Step 7: Emit Final Report

Generate the audit report in the required JSON schema:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3
  },
  "findings": [
    {
      "id": "F-001",
      "title": "No JSON-LD structured data on product pages",
      "severity": "high",
      "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
      "suggested_action": {
        "summary": "Add Product/Offer JSON-LD to every product page.",
        "priority": "high"
      }
    }
  ]
}
```

## Output

Returns a JSON object with:
- **site**: Domain name
- **audited_at**: ISO 8601 timestamp
- **summary**: Counts by severity
- **findings**: Array of finding objects

## Examples

### Example 1: Basic Audit
```
Input: "https://example.com"
Output: {
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {"total_findings": 5, "critical": 0, "high": 2, "medium": 3, "low": 0},
  "findings": [...]
}
```

### Example 2: Site with Critical Issues
```
Input: "https://problem-site.com"
Output: {
  "site": "problem-site.com",
  "audited_at": "2026-09-20T14:35:00Z",
  "summary": {"total_findings": 8, "critical": 2, "high": 3, "medium": 2, "low": 1},
  "findings": [
    {
      "id": "F-001",
      "title": "Meta robots NOINDEX detected",
      "severity": "critical",
      "evidence": "Found <meta name=\"robots\" content=\"noindex\"> on homepage",
      "suggested_action": {
        "summary": "Remove noindex directive or change to 'index, follow'",
        "priority": "critical"
      }
    },
    ...
  ]
}
```

## Error Handling

- **Invalid URL:** Return error message, do not proceed
- **Timeout (>5 min):** Return partial results with warning
- **Sub-skill failure:** Continue with remaining skills, note failure in report
- **No findings:** Return success message "No issues found - site appears well-optimized"

## Notes

- This is the entrypoint skill - it coordinates others but does not perform checks itself
- All sub-skills are in the same marketplace
- Output must follow the exact JSON schema specified in marketplace.json
- Be thorough but concise - actionable insights over verbose explanations
