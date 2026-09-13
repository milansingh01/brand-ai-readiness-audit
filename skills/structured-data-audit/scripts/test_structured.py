import json
import os
import sys
from pathlib import Path


# Allow this file to be executed directly from the scripts directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from skills.structured_data_audit.scripts.structured_checks import (  # noqa: E402
    run_checks,
)


SAMPLE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <title>Example Article</title>
    <meta name="description" content="An example article description.">
    <meta property="og:title" content="Example Article">
    <meta property="og:description" content="An example article description.">
    <meta property="og:url" content="https://example.com/article">
    <meta name="twitter:card" content="summary">
</head>
<body>
    <header>
        <nav aria-label="Primary navigation">
            <a href="/">Home</a>
        </nav>
    </header>

    <main>
        <article>
            <h1>Example Article</h1>
            <p>This is an example article.</p>
            <img src="/article.jpg" alt="Example article image">
        </article>
    </main>

    <footer>Example footer</footer>

    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Example Article",
        "author": {
            "@type": "Person",
            "name": "Example Author"
        },
        "datePublished": "2026-01-01",
        "dateModified": "2026-01-02"
    }
    </script>
</body>
</html>
"""


def main() -> int:
    observations = run_checks(SAMPLE_HTML)

    if not observations:
        print("No observations were returned.")
        return 1

    output = []

    for observation in observations:
        output.append(
            {
                "check": observation.check,
                "found": observation.found,
                "evidence": observation.evidence,
            }
        )

    print(json.dumps(output, indent=2, default=str))

    check_ids = {item["check"] for item in output}

    required_checks = {
        "SD-001",
        "SD-002",
        "SD-003",
        "SD-004",
        "SD-005",
        "SD-006",
        "SD-007",
        "SD-008",
        "SD-009",
        "SD-010",
        "SD-011",
        "SD-012",
        "SD-013",
    }

    missing_checks = required_checks - check_ids

    if missing_checks:
        print(
            "Missing expected checks:",
            ", ".join(sorted(missing_checks)),
        )
        return 1

    print("Structured-data smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())