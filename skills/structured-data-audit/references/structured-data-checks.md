# Structured Data Checks

The structured-data skill evaluates machine-readable information exposed
by the website.

The detector collects facts. The audit agent interprets their importance.

---

## SD-001 — Structured Data Presence

Check whether the page contains structured data.

Primary format:

`application/ld+json`

Also detect other supported structured-data mechanisms where practical.

Record:

- format
- number of blocks
- JSON validity

---

## SD-002 — Invalid JSON-LD

Attempt to parse JSON-LD blocks.

Record:

- number of blocks
- number of valid blocks
- number of invalid blocks
- parsing error information

---

## SD-003 — Schema Type Detection

Extract `@type` values.

Examples:

- Product
- Organization
- Article
- FAQPage
- BreadcrumbList
- LocalBusiness

Record detected types without assuming whether they are appropriate.

---

## SD-004 — Required/Important Property Presence

For recognized schema types, identify useful properties.

Examples:

Product:

- name
- description
- image
- offers

Article:

- headline
- author
- datePublished
- dateModified

Organization:

- name
- url
- logo

The detector should report presence/absence only.

---

## SD-005 — Schema Consistency

Compare structured-data values with visible page information where
possible.

Examples:

- product name
- price
- currency
- organization name
- article title

Record mismatches as observations.

---

## SD-006 — Duplicate or Conflicting Schema

Detect multiple structured-data blocks representing the same entity
with conflicting values.

Record:

- types
- conflicting properties
- values observed

---

## SD-007 — Breadcrumb Structure

Check whether breadcrumb structured data exists where appropriate.

Record:

- presence
- number of breadcrumb items
- item names/URLs