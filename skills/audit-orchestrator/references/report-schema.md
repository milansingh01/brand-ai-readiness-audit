# Audit Report Schema

The final audit report must contain:

## site

The audited website URL.

## audited_at

Timestamp indicating when the audit was performed.

## summary

Counts of findings by severity.

Example:

{
  "critical": 2,
  "high": 3,
  "medium": 4,
  "low": 1
}

## findings

Every finding should contain:

- id
- title
- severity
- evidence
- suggested_action

Optional fields may include:

- priority
- priority_reason
- check
- category

The report must preserve evidence collected by the audit tools.

The agent must not invent evidence that was not observed.