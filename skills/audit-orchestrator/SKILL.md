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
- Need to produce a comprehensive AI discoverability and engagement report
- Must coordinate multiple audit skills into a single output

## Inputs

- **url** (required): The website URL to audit
- **output_format** (optional): `json` (default) or `markdown`

## Procedure

### Step 1: Initialize Audit

1. Validate the URL format.
2. Record the audit timestamp in ISO 8601 format.
3. Initialize the observations and findings lists.

### Step 2: Invoke Sub-Skills

Run each sub-skill independently and collect its observations.

Do not assume that every check is applicable to every website.

Each sub-skill should distinguish between:

- `pass` — the check was performed and no issue was found
- `issue` — evidence indicates a real problem
- `unverified` — the check could not be reliably evaluated

A failure in one sub-skill must not stop the remaining applicable sub-skills.

### 2.1 Run crawl-render-audit

Input: `url`

Check:

- HTTP accessibility
- redirects
- robots.txt
- meta robots and X-Robots-Tag
- server-readable HTML
- JavaScript rendering dependence
- canonical signals
- important internal links
- other crawl and rendering barriers

### 2.2 Run structured-data-audit

Input: `url`

Check:

- JSON-LD
- structured data validity and consistency
- metadata
- heading structure
- semantic machine-readable content
- image accessibility signals

### 2.3 Run freshness-corroboration

Input: `url`

Check:

- freshness signals
- entity identity
- consistency across pages
- contradictions
- external corroboration where available

### 2.4 Run engagement-audit

Input: `url`

Check:

- navigation
- content hierarchy
- important hidden content
- internal linking
- interaction barriers
- mobile signals
- other factors affecting the visitor journey

Do not create a finding merely because an optional feature is absent.

Evaluate whether its absence materially affects AI discoverability, content interpretation, or user engagement.

### Step 3: Merge and Deduplicate

1. Combine observations from all applicable sub-skills.
2. Consider only observations marked `issue` when creating findings.
3. Remove duplicate findings describing the same underlying problem.
4. Do not merge findings that describe different problems merely because they affect the same area.
5. Assign unique IDs such as `F-001`, `F-002`, `F-003`.

### Step 4: Prioritize Findings

Prioritize findings using:

- severity
- impact
- scope
- evidence confidence
- importance of the affected discovery or visitor journey

Use severity as an important signal, but do not treat severity and priority as identical.

Order findings primarily by recommended priority:

1. **HIGH PRIORITY** — Major impact on AI discoverability or a core visitor journey; broad or important scope; strong evidence; should be addressed soon.
2. **MEDIUM PRIORITY** — Meaningful impact, but limited scope or moderate effect on an important area.
3. **LOW PRIORITY** — Minor impact, limited scope, or an optimization that does not materially block discovery or engagement.

Severity should be assigned separately:

1. **CRITICAL** — Site-wide or showstopper problem that severely prevents AI discoverability or a core visitor journey.
2. **HIGH** — Major problem affecting an important discovery or engagement path.
3. **MEDIUM** — Significant but scoped problem with meaningful impact.
4. **LOW** — Minor issue or optimization with limited impact.

Do not assign severity or priority solely from the check name.

Consider the website's context, scope, impact, evidence confidence, and whether the behavior may be intentional.

If evidence is insufficient, mark the check as `unverified` rather than creating a low-confidence finding.

Within the same priority level, order findings by severity and then impact.

### Step 5: Generate Summary

Count findings by severity.

The summary must contain:

```json
{
  "total_findings": 0,
  "critical": 0,
  "high": 0,
  "medium": 0,
  "low": 0
}