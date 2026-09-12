# Engagement Audit Checks

This skill evaluates signals related to user interaction and whether
important information/actions are exposed clearly enough for automated
systems to understand.

The detector reports observations only.

---

## EA-001 — Primary Calls to Action

Detect prominent calls to action.

Examples:

- Buy
- Book
- Contact
- Sign up
- Request demo
- Get started
- Apply

Record:

- visible text
- approximate location
- link/button destination when available

---

## EA-002 — Navigation Accessibility

Inspect primary navigation.

Record:

- navigation links
- link text
- destinations
- whether important sections appear reachable

---

## EA-003 — Important Content Hidden Behind Interaction

Detect possible content that appears to require:

- clicking
- opening tabs
- expanding accordions
- submitting forms
- JavaScript interaction

Record the interaction signal.

Do not assume that every interactive component is inaccessible.

---

## EA-004 — Form Presence

Detect forms and important input fields.

Record:

- number of forms
- field labels/placeholders
- form action
- input types

---

## EA-005 — Contact/Conversion Information

Detect useful conversion/contact signals.

Examples:

- phone number
- email
- contact link
- booking link
- inquiry form

Record what is present.

---

## EA-006 — Content Hierarchy

Inspect headings and visible content structure.

Record:

- H1 count
- heading hierarchy
- heading text
- obvious missing hierarchy signals

---

## EA-007 — Link Context

Inspect important links for descriptive text.

Record:

- link text
- destination
- generic labels such as "click here" where applicable

---

## EA-008 — Engagement Friction Signals

Record possible obstacles such as:

- important actions requiring multiple interactions
- empty buttons
- unclear link destinations
- interaction-dependent information

These are observations, not automatic severity assignments.