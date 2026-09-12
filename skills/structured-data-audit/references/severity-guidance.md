# Structured Data Severity Guidance

## Critical

Use only when structured data creates a serious discoverability problem
for an important entity or produces severe machine-readable conflicts.

## High

Use when important structured information is missing, invalid, or
substantially inconsistent.

Examples:

- invalid JSON-LD for an important entity
- important Product data cannot be parsed
- significant conflict between structured data and visible content

## Medium

Use for meaningful completeness or consistency problems.

Examples:

- missing important properties
- incomplete Organization information
- incomplete Article metadata
- missing breadcrumbs where they would materially help discovery

## Low

Use for minor schema completeness or optimization issues.

Severity should depend on:

1. Importance of the page/entity.
2. Whether the structured data is invalid or merely incomplete.
3. Whether the problem affects machine interpretation.
4. Whether corroborating page evidence exists.