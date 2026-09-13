---
name: freshness-corroboration
description: Audits content freshness, entity clarity, consistency, and web corroboration for AI citation and retrieval.
license: MIT
allowed-tools:
  - web_fetch
  - web_search
  - file_read
  - file_write
---

# Freshness & Corroboration Audit Skill

## When to Use

Use when checking content freshness, entity clarity, consistency, and external trust signals for AI citation.

## Inputs

- **url** (required): Website URL to audit

## Reasoning Rules

- Absence of a visible date does not automatically mean content is stale.
- Evaluate freshness based on the type of content. Dates are more important for news, articles, prices, policies, events, and other time-sensitive information than for evergreen pages.
- Do not assume that lack of a Wikipedia or Wikidata entry means an entity is ambiguous.
- Use multiple identity signals such as organization name, domain, About/Contact information, structured data, sameAs links, and consistent references.
- External corroboration is supporting evidence, not a mandatory requirement for every website.
- Conflicting information should only become a finding when the conflict is material and supported by evidence.
- If external corroboration cannot be reliably checked, mark it `unverified`.

## Checks

### 1. Entity Identity

- Detection: Look for sufficient and consistent identity signals across the website and available external sources.
- Consider organization name, domain, About/Contact information, structured data, sameAs links, and other identifiers.
- Absence of Wikipedia or Wikidata alone is not sufficient evidence of ambiguity.
- Mechanism: Weak or conflicting identity signals can make it harder for AI systems to distinguish the intended entity from similarly named entities.
- Fix: Strengthen consistent identity and disambiguation signals.

### 2. Freshness Signals

- Detection: Check visible dates, `<time>` elements, metadata, structured-data dates, and available `Last-Modified` information.
- Evaluate whether dates are relevant to the type of content.
- Evidence should describe the absence of freshness signals, not claim that the content is stale unless staleness is actually supported.
- Mechanism: For time-sensitive content, unclear freshness can reduce confidence in whether information is current.
- Fix: Add accurate publication or modification dates where appropriate.

### 3. Conflicting Information

- Detection: Compare important information across multiple accessible pages when possible.
- Look for material differences in organization details, addresses, contact information, product information, policies, or other important facts.
- Mechanism: Material contradictions can make it difficult for AI systems and visitors to determine which information is current.
- Fix: Resolve conflicting information and maintain consistent authoritative details.

### 4. External Corroboration

- Detection: Search for reliable independent references to the entity or important claims when web search is available.
- Only report lack of corroboration when a reasonable external search was actually performed.
- Lack of third-party references is not automatically a defect.
- Mechanism: Independent sources can strengthen confidence in important entity and factual claims.
- Fix: Where appropriate, build legitimate external references through authoritative publications, organizations, directories, or other relevant sources.

### 5. Entity Disambiguation Signals

- Detection: Check for `sameAs`, unique identifiers, organization details, and other explicit identity signals.
- Treat this as supporting evidence for entity clarity rather than an automatic requirement.
- Mechanism: Clear identity signals can reduce confusion with similarly named entities.
- Fix: Add appropriate disambiguation signals where they provide meaningful value.

## Procedure

1. Validate the input URL.
2. Fetch the target page where possible.
3. Record the final URL, HTTP status, response headers, and available HTML.
4. Inspect freshness and identity signals.
5. Inspect multiple relevant pages when available.
6. Use external search for corroboration when available.
7. Distinguish `pass`, `issue`, and `unverified`.
8. Convert supported issues into structured observations with evidence.
9. Do not create findings solely because an optional signal is absent.
10. Do not modify the website or perform authenticated/destructive actions.

## Output

Return structured observations such as:

```json
{
  "check": "FC-001",
  "status": "issue",
  "evidence": "Two accessible pages contain different addresses for the same organization.",
  "details": {
    "impact": "major",
    "scope": "site"
  }
}