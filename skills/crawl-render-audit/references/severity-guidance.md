# Crawl and Render Severity Guidance

The audit agent uses this guidance when converting crawl observations
into findings.

Severity is contextual.

## Critical

Use when the observation indicates that important public content is
directly prevented from being discovered or accessed.

Examples:

- important page has `noindex`
- important page consistently returns 5xx
- important page cannot be fetched because of a blocking access rule

## High

Use when the website is technically reachable but substantial content
may be unavailable or difficult for automated retrieval.

Examples:

- important content appears dependent on client-side rendering
- raw HTML contains almost no meaningful content despite substantial
page functionality
- relevant crawler access is restricted

## Medium

Use for meaningful technical weaknesses that reduce reliability or
discoverability but do not directly block access.

Examples:

- missing canonical
- excessive page size
- many render-blocking resources
- missing fallback content where rendering dependency is established

## Low

Use for minor optimization opportunities or weak signals.

Severity should consider:

1. Whether the affected page is important.
2. Whether the problem blocks access or only reduces quality.
3. Whether supporting observations confirm the problem.
4. Whether the issue affects one page or many pages.