import sys
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared.http_client import fetch_page
from structured_checks import run_checks


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python test_structured.py https://example.com")
        return

    url = sys.argv[1]

    print(f"\nAuditing structured data: {url}")
    print("=" * 60)

    try:
        response = fetch_page(url)
    except Exception as e:
        print(json.dumps({
            "check": "http_access",
            "found": True,
            "evidence": str(e)
        }, indent=2))
        return

    observations = run_checks(response.text)

    output = [
        observation.to_dict()
        for observation in observations
    ]

    print("\nOBSERVATIONS")
    print("=" * 60)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()