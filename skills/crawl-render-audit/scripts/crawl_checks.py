from bs4 import BeautifulSoup

from shared.models import Observation


def check_http_status(response) -> Observation:
    """
    Check whether the page returned a successful HTTP response.
    """

    status_code = getattr(response, "status_code", None)

    return Observation(
        check="CR-001",
        found=status_code is None or status_code >= 400,
        evidence={
            "status_code": status_code
        },
        details={
            "issue": "HTTP error response"
            if status_code is not None and status_code >= 400
            else "HTTP response is accessible"
        }
    )


def check_noindex(html: str, response) -> Observation:
    """
    Check for noindex directives in meta robots and X-Robots-Tag.
    """

    soup = BeautifulSoup(html, "html.parser")

    meta_noindex = []

    for tag in soup.find_all(
        "meta",
        attrs={"name": lambda value: value and value.lower() == "robots"}
    ):
        content = tag.get("content", "")

        if "noindex" in content.lower():
            meta_noindex.append(content)

    x_robots_tag = ""

    headers = getattr(response, "headers", {}) or {}

    for key, value in headers.items():
        if key.lower() == "x-robots-tag":
            x_robots_tag = value
            break

    header_noindex = (
        "noindex" in x_robots_tag.lower()
        if x_robots_tag
        else False
    )

    found = bool(meta_noindex or header_noindex)

    return Observation(
        check="CR-002",
        found=found,
        evidence={
            "meta_robots_noindex": meta_noindex,
            "x_robots_tag": x_robots_tag or None
        },
        details={
            "sources": [
                source
                for source, present in [
                    ("meta_robots", bool(meta_noindex)),
                    ("x_robots_tag", header_noindex)
                ]
                if present
            ]
        }
    )


def check_empty_or_thin_html(html: str) -> Observation:
    """
    Detect pages with very little readable HTML content.
    """

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "template"]
    ):
        element.decompose()

    text = " ".join(soup.stripped_strings)

    text_length = len(text)

    # Very small amounts of visible text can indicate
    # a page that depends heavily on client-side rendering.
    found = text_length < 200

    return Observation(
        check="CR-003",
        found=found,
        evidence={
            "visible_text_length": text_length
        },
        details={
            "threshold": 200
        }
    )


def check_javascript_rendering(html: str) -> Observation:
    """
    Look for indicators that meaningful content may depend
    on JavaScript rendering.
    """

    soup = BeautifulSoup(html, "html.parser")

    visible_text = " ".join(soup.stripped_strings)

    script_count = len(soup.find_all("script"))

    body = soup.body

    body_html_length = len(body.decode_contents()) if body else 0

    # Common SPA/root-container indicators.
    root_containers = []

    for element_id in [
        "root",
        "app",
        "__next",
        "__nuxt"
    ]:
        if soup.find(id=element_id):
            root_containers.append(element_id)

    found = (
        len(visible_text) < 200
        and (
            script_count > 0
            or body_html_length > 0
            or bool(root_containers)
        )
    )

    return Observation(
        check="CR-004",
        found=found,
        evidence={
            "visible_text_length": len(visible_text),
            "script_count": script_count,
            "body_html_length": body_html_length,
            "root_containers": root_containers
        },
        details={
            "possible_client_side_rendering": found
        }
    )


def check_noscript(html: str) -> Observation:
    """
    Check whether the page provides a noscript fallback.
    """

    soup = BeautifulSoup(html, "html.parser")

    noscript_tags = soup.find_all("noscript")

    useful_noscript = []

    for tag in noscript_tags:
        text = " ".join(tag.stripped_strings).strip()

        if text:
            useful_noscript.append(text[:500])

    return Observation(
        check="CR-005",
        found=len(useful_noscript) > 0,
        evidence={
            "noscript_count": len(noscript_tags),
            "useful_noscript": useful_noscript
        },
        details={
            "has_noscript_fallback": bool(useful_noscript)
        }
    )


def check_spa_indicators(html: str) -> Observation:
    """
    Detect common indicators of a client-side single-page application.
    """

    soup = BeautifulSoup(html, "html.parser")

    indicators = []

    for element_id in [
        "root",
        "app",
        "__next",
        "__nuxt"
    ]:
        if soup.find(id=element_id):
            indicators.append(f"id={element_id}")

    script_sources = []

    for script in soup.find_all("script", src=True):
        src = script.get("src")

        if src:
            script_sources.append(src)

    framework_terms = [
        "webpack",
        "vite",
        "react",
        "next",
        "nuxt",
        "angular",
        "vue"
    ]

    for src in script_sources:
        src_lower = src.lower()

        for term in framework_terms:
            if term in src_lower:
                indicators.append(f"script:{term}")

    return Observation(
        check="CR-006",
        found=len(indicators) > 0,
        evidence={
            "indicators": indicators,
            "script_sources": script_sources[:50]
        },
        details={
            "possible_spa": len(indicators) > 0
        }
    )


def run_checks(html: str, response):
    """
    Run all crawl and rendering checks.

    Each check reports an objective observation.
    Severity and suggested actions are decided by
    the orchestration layer.
    """

    return [
        check_http_status(response),
        check_noindex(html, response),
        check_empty_or_thin_html(html),
        check_javascript_rendering(html),
        check_noscript(html),
        check_spa_indicators(html),
    ]