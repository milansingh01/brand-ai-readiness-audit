import json


# ============================================================
# OBSERVATION VALIDATION
# ============================================================

def validate_observation(observation):
    """
    Validate the normalized output produced by an audit skill.

    Observations use the tri-state model:

        pass
        issue
        unverified
    """

    required_fields = [
        "check",
        "status",
        "evidence",
    ]

    missing = [
        field
        for field in required_fields
        if field not in observation
    ]

    if missing:
        return missing

    valid_statuses = {
        "pass",
        "issue",
        "unverified"
    }

    if observation["status"] not in valid_statuses:
        return [
            "status must be one of: pass, issue, unverified"
        ]

    return []


# ============================================================
# FINDING VALIDATION
# ============================================================

def validate_finding(finding):
    """
    Validate the final interpreted finding.
    """

    required_fields = [
        "id",
        "title",
        "severity",
        "evidence",
        "suggested_action",
    ]

    missing = [
        field
        for field in required_fields
        if field not in finding
    ]

    if missing:
        return missing

    valid_severities = {
        "critical",
        "high",
        "medium",
        "low"
    }

    if finding["severity"] not in valid_severities:
        return [
            "severity must be one of: "
            "critical, high, medium, low"
        ]

    return []


# ============================================================
# REPORT VALIDATION
# ============================================================

def validate_report(report):
    """
    Validate the final marketplace report schema.
    """

    required_fields = [
        "site",
        "audited_at",
        "summary",
        "findings"
    ]

    missing = [
        field
        for field in required_fields
        if field not in report
    ]

    if missing:
        return missing

    required_summary_fields = [
        "total_findings",
        "critical",
        "high",
        "medium",
        "low"
    ]

    missing_summary = [
        field
        for field in required_summary_fields
        if field not in report["summary"]
    ]

    if missing_summary:
        return [
            f"summary.{field}"
            for field in missing_summary
        ]

    return []


# ============================================================
# TEST
# ============================================================

def main():

    print("=" * 60)
    print("ORCHESTRATOR SCHEMA TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Observation
    # --------------------------------------------------------

    observation = {
        "check": "meta_robots",
        "status": "issue",
        "evidence": "Found noindex directive",
        "details": {
            "source": "meta"
        }
    }

    missing = validate_observation(
        observation
    )

    print("\nObservation:")
    print(
        json.dumps(
            observation,
            indent=2
        )
    )

    print("\nObservation validation:")
    print(
        "PASS"
        if not missing
        else f"FAIL: {missing}"
    )

    # --------------------------------------------------------
    # Finding
    # --------------------------------------------------------

    finding = {
        "id": "F-001",
        "title": "Important page is blocked from indexing",
        "severity": "high",
        "evidence": "Found noindex directive",
        "suggested_action": {
            "summary": (
                "Review the noindex directive and remove it "
                "from pages that should be discoverable."
            ),
            "priority": "high"
        },
        "priority": "high",
        "priority_reason": (
            "The issue can directly prevent an important "
            "page from being discovered."
        )
    }

    missing = validate_finding(
        finding
    )

    print("\nFinding:")
    print(
        json.dumps(
            finding,
            indent=2
        )
    )

    print("\nFinding validation:")
    print(
        "PASS"
        if not missing
        else f"FAIL: {missing}"
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    report = {
        "site": "https://example.com",
        "audited_at": (
            "2026-09-13T00:00:00+00:00"
        ),
        "summary": {
            "total_findings": 1,
            "critical": 0,
            "high": 1,
            "medium": 0,
            "low": 0
        },
        "findings": [
            finding
        ]
    }

    missing = validate_report(
        report
    )

    print("\nFinal report:")
    print(
        json.dumps(
            report,
            indent=2
        )
    )

    print("\nReport validation:")
    print(
        "PASS"
        if not missing
        else f"FAIL: {missing}"
    )


if __name__ == "__main__":
    main()