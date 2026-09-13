import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCRIPT_DIR = Path(__file__).resolve().parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


from shared.http_client import fetch_page
from engagement_checks import run_checks


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python test_engagement.py https://example.com")
        return 1

    url = sys.argv[1]

    print(f"\nAuditing engagement: {url}")
    print("=" * 60)

    try:
        response = fetch_page(url)
    except Exception as error:
        print(
            json.dumps(
                {
                    "check": "http_access",
                    "found": True,
                    "evidence": str(error),
                },
                indent=2,
            )
        )
        return 1

    observations = run_checks(
        response.text,
        response.url,
    )

    output = [
        observation.to_dict()
        for observation in observations
    ]

    print("\nOBSERVATIONS")
    print("=" * 60)
    print(json.dumps(output, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())