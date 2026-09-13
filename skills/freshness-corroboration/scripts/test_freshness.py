# skills/freshness-corroboration/scripts/test_freshness.py
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.http_client import fetch_page
from skills.freshness_corroboration.scripts.freshness_checks import run_checks


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python test_freshness.py <url>")
        return 1

    url = sys.argv[1]

    try:
        response = fetch_page(url)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                },
                indent=2,
            )
        )
        return 1

    observations = run_checks(
        html=response.text,
        headers=response.headers,
        url=response.url,
        audit_time=datetime.now(timezone.utc),
    )

    output = []

    for observation in observations:
        if hasattr(observation, "to_dict"):
            output.append(observation.to_dict())
        else:
            output.append(
                {
                    "check_id": getattr(observation, "check_id", None),
                    "check_name": getattr(observation, "check_name", None),
                    "status": getattr(observation, "status", None),
                    "finding": getattr(observation, "finding", None),
                    "evidence": getattr(observation, "evidence", []),
                    "reasoning": getattr(observation, "reasoning", None),
                    "severity": getattr(observation, "severity", None),
                    "priority": getattr(observation, "priority", None),
                    "suggested_action": getattr(
                        observation,
                        "suggested_action",
                        "",
                    ),
                }
            )

    print(
        json.dumps(
            {
                "url": response.url,
                "observations": output,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())