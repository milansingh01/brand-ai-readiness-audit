# Crawl and Render Checks

This reference defines the checks performed by the crawl-render-audit skill.

The executable scripts should collect objective observations only.
Severity and suggested actions are determined by the audit agent using
this taxonomy and the severity guidance.

---

## CR-001 — Meta Robots Noindex

Check whether the HTML contains a robots meta directive containing
`noindex`.

Possible evidence:

- `<meta name="robots" content="noindex">`
- `<meta name="googlebot" content="noindex">`

Observation should identify:

- directive
- source
- affected page

Do not automatically assign severity.

---

## CR-002 — X-Robots-Tag Noindex

Check HTTP response headers for:

`X-Robots-Tag: noindex`

Observation should contain:

- header value
- affected URL

---

## CR-003 — HTTP Access Failure

Check HTTP response status.

Record:

- status code
- final URL
- redirect information if available

Important classes:

- 4xx
- 5xx
- request timeout
- connection failure
- TLS failure

Do not automatically assign severity.

---

## CR-004 — Empty or Very Low-Content HTML

Measure the amount of meaningful text available in the raw HTML.

The detector should report:

- total HTML size
- extracted text length
- extracted text sample if useful

A low text count alone should not automatically mean the page is
unusable because some pages intentionally contain little text.

---

## CR-005 — Client-Side Rendering Signal

Look for signals that content may depend heavily on JavaScript.

Possible signals:

- root elements such as `#root`
- root elements such as `#app`
- framework-related script references
- very small initial HTML
- script-heavy document

These are signals, not proof that the site is inaccessible.

---

## CR-006 — Missing Noscript Fallback

If strong client-side rendering signals are detected, check whether
the document contains meaningful `<noscript>` content.

The absence of noscript should be treated as supporting evidence rather
than an automatic failure.

---

## CR-007 — Missing Canonical

Check whether the document contains:

`<link rel="canonical" ...>`

Record:

- whether canonical exists
- canonical URL if present

---

## CR-008 — Robots.txt Restriction

Fetch `/robots.txt` and inspect rules relevant to automated crawling.

Record:

- whether robots.txt exists
- relevant User-agent groups
- Disallow rules
- Allow rules
- whether the requested path appears blocked

Do not assume that `Disallow: /` universally blocks every crawler.
Evaluate the applicable user-agent rules.

---

## CR-009 — Performance Signals

Collect objective page-size and script information.

Record:

- response size
- number of script tags
- number of potentially render-blocking scripts
- number of external scripts

These measurements are signals rather than automatic severity assignments.