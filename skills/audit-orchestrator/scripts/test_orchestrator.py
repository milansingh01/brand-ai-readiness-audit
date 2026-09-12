import json


def validate_observation(observation):
    """
    Validate the output produced by an audit skill.
    """

    required_fields = [
        "check",
        "found",
        "evidence",
    ]

    missing = [
        field
        for field in required_fields
        if field not in observation
    ]

    return missing


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

    return missing


def main():
    print("=" * 60)
    print("ORCHESTRATOR SCHEMA TEST")
    print("=" * 60)

    observation = {
        "check": "meta_robots",
        "found": True,
        "evidence": "Found noindex directive",
        "details": {
            "source": "meta"
        }
    }

    missing = validate_observation(observation)

    print("\nObservation:")
    print(json.dumps(observation, indent=2))

    print("\nObservation validation:")
    print("PASS" if not missing else f"FAIL: missing {missing}")

    finding = {
        "id": "CR-001",
        "title": "Important page is blocked from indexing",
        "severity": "critical",
        "evidence": "Found noindex directive",
        "suggested_action": (
            "Review the noindex directive and remove it from pages "
            "that should be discoverable."
        ),
        "priority": 1,
        "priority_reason": (
            "The issue can directly prevent an important page "
            "from being discovered."
        )
    }

    missing = validate_finding(finding)

    print("\nFinding:")
    print(json.dumps(finding, indent=2))

    print("\nFinding validation:")
    print("PASS" if not missing else f"FAIL: missing {missing}")


if __name__ == "__main__":
    main()