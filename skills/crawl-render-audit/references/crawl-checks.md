# Crawl and Render Checks

This reference defines the evidence checks performed by the
crawl-render-audit skill.

The executable implementation should collect objective observations.
The audit agent determines whether those observations represent
material problems.

Severity and suggested actions are assigned by the audit agent using
the website context and severity guidance.

---

## CR-001 — Meta Robots Noindex

Check whether the HTML contains page-level robots directives
containing `noindex`.

Relevant directives may include:

- `<meta name="robots" content="noindex">`
- `<meta name="googlebot" content="noindex">`
- other relevant crawler-specific robots directives

Observation should identify:

- directive name
- directive value
- affected page

A noindex directive can be a material discoverability problem when
applied to important public content.

Do not assign severity solely from the presence of the directive.

---

## CR-002 — X-Robots-Tag Noindex

Check HTTP response headers for:

`X-Robots-Tag: noindex`

Observation should contain:

- header value
- whether `noindex` is present
- affected URL when available

Do not treat a missing header as an issue.

---

## CR-003 — HTTP Access Failure

Check HTTP response status and available access information.

Record:

- status code
- final URL
- redirects when available
- request failures when available

Important classes include:

- 4xx
- 5xx
- timeout
- connection failure
- TLS failure

A local TLS, proxy, DNS, or tool failure must not automatically be
reported as evidence that the website blocks AI crawlers.

If no reliable website evidence is available, mark the check
`unverified`.

---

## CR-004 — Empty or Very Low-Content HTML

Measure meaningful text available in raw HTML.

Record:

- HTML size
- extracted text length
- useful text sample when appropriate

A low text count is a signal rather than automatic proof of a defect.

Consider the purpose of the page and whether important content is
actually missing from the server-readable HTML.

---

## CR-005 — Client-Side Rendering Signal

Look for signals that content may depend heavily on JavaScript.

Possible signals include:

- root elements such as `#root`
- root elements such as `#app`
- framework-related script references
- very small initial HTML
- script-heavy documents

These are signals, not proof that the site is inaccessible.

A finding should be created only when there is evidence that important
content is unavailable or substantially reduced without rendering.

---

## CR-006 — Missing Noscript Fallback

Check whether the document contains meaningful `<noscript>` content.

The absence of a noscript fallback is supporting evidence only.

Do not report missing noscript as a standalone defect when important
content is already available in server-readable HTML.

---

## CR-007 — Missing Canonical

Check whether the document contains:

`<link rel="canonical" ...>`

Record:

- whether a canonical exists
- canonical URL when present
- page URL when available

Missing canonical should not automatically become a major finding.

Consider whether URL duplication or ambiguity makes the absence
material for this website.

---

## CR-008 — Robots.txt Restriction

Inspect `/robots.txt` where it can be reliably obtained.

Record:

- whether robots.txt is available
- User-agent groups
- Disallow rules
- Allow rules
- applicable restrictions when the requested path is known

Do not assume that `Disallow: /` universally blocks every crawler.

Evaluate the applicable User-agent group and requested path.

Targeted restrictions on specific AI crawlers are not equivalent to a
site-wide crawler block.

---

## CR-009 — Performance Signals

Collect objective page-size and script information.

Record:

- response/page size
- number of script tags
- number of external scripts
- number of potentially render-blocking scripts

These are signals rather than automatic findings.

Do not treat a fixed page-size or script-count threshold as guaranteed
crawler failure.

The agent should consider whether the evidence indicates a material
loading or rendering problem.

---

## CR-010 — Internal Link Discovery

Identify important internal links from the audited page where possible.

Record:

- observed links
- link text
- destination

Consider whether important sections appear discoverable through normal
navigation and internal links.

Do not claim that a page is orphaned when only one page has been
inspected. Orphan status requires evidence from multiple pages or
broader crawl inspection.

---

## Observation Status

Each check should use one of:

- `pass` — the check was performed and no material issue was established
- `issue` — evidence indicates a potential real problem
- `unverified` — the check could not be reliably evaluated

The `issue` status is evidence for the audit agent to interpret. It does
not by itself determine severity or priority.