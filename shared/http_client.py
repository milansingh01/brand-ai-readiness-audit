import requests


DEFAULT_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; BrandAIReadinessAudit/1.0)"
    )
}


def fetch_page(url: str):
    """
    Fetch a webpage using a consistent timeout and user agent.

    SSL verification remains enabled.
    """

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=DEFAULT_TIMEOUT,
            allow_redirects=True,
        )

        return response

    except requests.exceptions.SSLError as e:
        raise RuntimeError(
            f"TLS/SSL certificate validation failed for {url}: {e}"
        )

    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Request timed out while accessing {url}"
        )

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Unable to fetch {url}: {e}"
        )


def fetch_text(url: str):
    """
    Convenience wrapper returning response text.
    """

    response = fetch_page(url)

    return response.text