# Audit Report Schema

The final audit report must contain the following top-level fields:

## site

The audited website URL.

## audited_at

Timestamp indicating when the audit was performed.

Use an ISO 8601 timestamp.

## summary

Counts of findings by severity.

The summary must contain:

```json
{
  "total_findings": 0,
  "critical": 0,
  "high": 0,
  "medium": 0,
  "low": 0
}