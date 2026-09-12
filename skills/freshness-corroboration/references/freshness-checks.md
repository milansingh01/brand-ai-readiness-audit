# Freshness and Corroboration Checks

This skill evaluates whether important website information appears
current and whether important claims can be corroborated by multiple
signals.

---

## FC-001 — Published Date

Detect publication dates from:

- visible page content
- metadata
- JSON-LD
- OpenGraph metadata where applicable

Record all detected dates and their sources.

---

## FC-002 — Modified Date

Detect:

- dateModified
- Last-Modified HTTP header
- visible update timestamps
- other explicit modification metadata

Record source and value.

---

## FC-003 — Conflicting Dates

Compare dates from different sources.

Examples:

- visible date differs from JSON-LD
- dateModified predates datePublished
- HTTP Last-Modified conflicts with page metadata

Record exact values and sources.

---

## FC-004 — Stale Content Signal

Estimate content age using available dates.

Do not automatically call old content incorrect.

Record:

- detected date
- current audit date
- approximate age

---

## FC-005 — Missing Freshness Signals

Check whether an important content type lacks useful date/freshness
information.

Examples:

- article without publication date
- product information without update signal
- frequently changing information without freshness metadata

---

## FC-006 — Claim Corroboration

Where practical, compare important facts across independent website
signals.

Examples:

- visible price vs structured-data price
- visible product name vs Product schema name
- article title vs metadata title
- organization name vs Organization schema

Record agreement or mismatch.

---

## FC-007 — Contradictory Information

Identify explicit conflicts between available sources.

Record:

- claim
- source A
- value A
- source B
- value B