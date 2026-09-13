import sys
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.http_client import fetch_page
from crawl_checks import run_checks


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print("python test_crawl.py https://example.com")
        return

    url = sys.argv[1]

    print(f"\nAuditing: {url}")
    print("=" * 60)

    try:
        response = fetch_page(url)

    except Exception as error:
        print("\nFETCH OBSERVATION")
        print("=" * 60)

        print(
            json.dumps(
                {
                    "check": "CR-003",
                    "status": "unverified",
                    "evidence": (
                        "The page could not be fetched by the "
                        "current execution environment."
                    ),
                    "details": {
                        "url": url,
                        "error": str(error),
                        "interpretation": (
                            "Do not treat a local TLS, proxy, "
                            "DNS, or tool failure as proof that "
                            "the website blocks AI crawlers."
                        )
                    }
                },
                indent=2
            )
        )

        return

    print(f"Final URL : {response.url}")
    print(f"Status    : {response.status_code}")
    print(f"Size      : {len(response.content)} bytes")

    observations = run_checks(
        response.text,
        response
    )

    print("\nOBSERVATIONS")
    print("=" * 60)

    output = [
        observation.to_dict()
        for observation in observations
    ]

    print(
        json.dumps(
            output,
            indent=2
        )
    )


if __name__ == "__main__":
    main()