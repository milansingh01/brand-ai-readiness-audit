from bs4 import BeautifulSoup

from shared.models import Observation


def make_observation(check, status, evidence, details=None):
    """
    Create a normalized observation using the tri-state model:

    pass      = check completed and no issue was found
    issue     = evidence indicates a potential issue
    unverified = check could not be reliably evaluated
    """

    return Observation(
        check=check,
        status=status,
        evidence=evidence,
        details=details or {}
    )


def check_meta_robots_noindex(html: str) -> Observation:
    """
    CR-001 — Check page-level robots directives for noindex.
    """

    soup = BeautifulSoup(html, "html.parser")

    directives = []

    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("http-equiv") or ""

        if str(name).lower() in {
            "robots",
            "googlebot",
            "bingbot"
        }:
            content = tag.get("content", "")

            if "noindex" in content.lower():
                directives.append({
                    "name": name,
                    "content": content
                })

    status = "issue" if directives else "pass"

    return make_observation(
        "CR-001",
        status,
        {
            "meta_noindex": directives
        },
        {
            "sources": [
                item["name"]
                for item in directives
            ]
        }
    )


def check_x_robots_noindex(response) -> Observation:
    """
    CR-002 — Check X-Robots-Tag response header for noindex.
    """

    headers = getattr(response, "headers", {}) or {}

    header_value = None

    for key, value in headers.items():
        if key.lower() == "x-robots-tag":
            header_value = value
            break

    if header_value is None:
        return make_observation(
            "CR-002",
            "pass",
            {
                "x_robots_tag": None,
                "noindex": False
            }
        )

    noindex = "noindex" in str(header_value).lower()

    return make_observation(
        "CR-002",
        "issue" if noindex else "pass",
        {
            "x_robots_tag": header_value,
            "noindex": noindex
        }
    )


def check_http_access(response) -> Observation:
    """
    CR-003 — Check HTTP access status.

    The fetch layer is responsible for reporting exceptions.
    If a response exists, record its status and final URL.
    """

    status_code = getattr(response, "status_code", None)
    final_url = getattr(response, "url", None)

    if status_code is None:
        return make_observation(
            "CR-003",
            "unverified",
            {
                "status_code": None,
                "final_url": final_url
            },
            {
                "reason": "No HTTP status code was available."
            }
        )

    status = (
        "issue"
        if status_code >= 400
        else "pass"
    )

    return make_observation(
        "CR-003",
        status,
        {
            "status_code": status_code,
            "final_url": final_url
        },
        {
            "http_error": status_code >= 400
        }
    )


def check_empty_or_thin_html(html: str, response=None) -> Observation:
    """
    CR-004 — Measure meaningful text in raw HTML.

    A low text count is only a signal. It is not automatically
    proof that the page is unusable.
    """

    soup = BeautifulSoup(html, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "template"]
    ):
        element.decompose()

    text = " ".join(soup.stripped_strings)
    text_length = len(text)

    html_size = len(html.encode("utf-8", errors="ignore"))

    # This threshold identifies a possible thin/empty page.
    # The agent must consider page purpose and context.
    low_content = text_length < 200

    return make_observation(
        "CR-004",
        "issue" if low_content else "pass",
        {
            "html_size_bytes": html_size,
            "extracted_text_length": text_length,
            "text_sample": text[:500]
        },
        {
            "low_content_signal": low_content,
            "threshold": 200
        }
    )


def check_client_side_rendering(html: str) -> Observation:
    """
    CR-005 — Detect signals of client-side rendering.

    These signals do not prove an accessibility problem.
    """

    soup = BeautifulSoup(html, "html.parser")

    visible_text = " ".join(
        soup.stripped_strings
    )

    script_tags = soup.find_all("script")
    script_count = len(script_tags)

    body = soup.body
    body_html_length = (
        len(body.decode_contents())
        if body
        else 0
    )

    root_containers = []

    for element_id in [
        "root",
        "app",
        "__next",
        "__nuxt"
    ]:
        if soup.find(id=element_id):
            root_containers.append(element_id)

    framework_terms = [
        "webpack",
        "vite",
        "react",
        "next",
        "nuxt",
        "angular",
        "vue"
    ]

    framework_scripts = []

    for script in soup.find_all("script", src=True):
        src = script.get("src", "")
        src_lower = src.lower()

        for term in framework_terms:
            if term in src_lower:
                framework_scripts.append({
                    "term": term,
                    "src": src
                })

    strong_signal = (
        len(visible_text) < 200
        and (
            bool(root_containers)
            or bool(framework_scripts)
            or script_count >= 10
        )
    )

    return make_observation(
        "CR-005",
        "issue" if strong_signal else "pass",
        {
            "visible_text_length": len(visible_text),
            "script_count": script_count,
            "body_html_length": body_html_length,
            "root_containers": root_containers,
            "framework_scripts": framework_scripts[:50]
        },
        {
            "client_side_rendering_signal": strong_signal,
            "note": (
                "Rendering signals are not proof of a defect. "
                "Important content must be evaluated separately."
            )
        }
    )


def check_missing_noscript_fallback(html: str) -> Observation:
    """
    CR-006 — Check for meaningful noscript fallback.

    Absence is supporting evidence only and should not be treated
    as an automatic failure.
    """

    soup = BeautifulSoup(html, "html.parser")

    noscript_tags = soup.find_all("noscript")

    useful_noscript = []

    for tag in noscript_tags:
        text = " ".join(
            tag.stripped_strings
        ).strip()

        if text:
            useful_noscript.append(
                text[:500]
            )

    return make_observation(
        "CR-006",
        "pass",
        {
            "noscript_count": len(noscript_tags),
            "useful_noscript": useful_noscript
        },
        {
            "has_noscript_fallback": bool(
                useful_noscript
            ),
            "interpretation": (
                "Missing noscript is not an issue by itself. "
                "Evaluate together with rendering dependency."
            )
        }
    )


def check_canonical(html: str, response=None) -> Observation:
    """
    CR-007 — Check canonical URL signals.
    """

    soup = BeautifulSoup(html, "html.parser")

    canonical_tags = soup.find_all(
        "link",
        attrs={
            "rel": lambda value: (
                value and
                (
                    "canonical" in value
                    if isinstance(value, list)
                    else "canonical" in str(value).lower()
                )
            )
        }
    )

    canonical_urls = [
        tag.get("href")
        for tag in canonical_tags
        if tag.get("href")
    ]

    page_url = getattr(response, "url", None)

    if not canonical_urls:
        # Missing canonical is a contextual weakness, not an
        # automatic major discoverability failure.
        return make_observation(
            "CR-007",
            "pass",
            {
                "canonical_present": False,
                "canonical_url": None,
                "page_url": page_url
            },
            {
                "interpretation": (
                    "Canonical is absent. Evaluate whether URL "
                    "duplication or ambiguity makes this material."
                )
            }
        )

    return make_observation(
        "CR-007",
        "pass",
        {
            "canonical_present": True,
            "canonical_url": canonical_urls[0],
            "all_canonical_urls": canonical_urls,
            "page_url": page_url
        }
    )


def check_performance_signals(html: str) -> Observation:
    """
    CR-009 — Collect objective performance-related signals.

    These are signals only and do not automatically constitute
    a finding.
    """

    soup = BeautifulSoup(html, "html.parser")

    scripts = soup.find_all("script")

    external_scripts = []
    render_blocking_candidates = []

    for script in scripts:
        src = script.get("src")

        if src:
            external_scripts.append(src)

            has_async = script.has_attr("async")
            has_defer = script.has_attr("defer")

            if not has_async and not has_defer:
                render_blocking_candidates.append(src)

    html_size = len(
        html.encode(
            "utf-8",
            errors="ignore"
        )
    )

    return make_observation(
        "CR-009",
        "pass",
        {
            "html_size_bytes": html_size,
            "script_count": len(scripts),
            "external_script_count": len(external_scripts),
            "potentially_render_blocking_scripts": len(
                render_blocking_candidates
            )
        },
        {
            "external_scripts": external_scripts[:50],
            "render_blocking_candidates": (
                render_blocking_candidates[:50]
            ),
            "interpretation": (
                "Performance measurements are signals. "
                "Determine material impact using context."
            )
        }
    )


def check_internal_link_discovery(
    html: str,
    response=None
) -> Observation:
    """
    CR-010 — Inspect internal links available from the audited page.

    This check does not claim that any page is orphaned because
    only one page has been inspected.
    """

    soup = BeautifulSoup(html, "html.parser")

    page_url = getattr(response, "url", None)

    links = []

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()

        if not href:
            continue

        text = " ".join(
            anchor.stripped_strings
        ).strip()

        links.append({
            "href": href,
            "text": text[:200]
        })

    return make_observation(
        "CR-010",
        "pass",
        {
            "page_url": page_url,
            "internal_link_count_observed": len(links),
            "links": links[:200]
        },
        {
            "interpretation": (
                "Links were collected from the audited page. "
                "Orphan status requires inspection of multiple pages."
            )
        }
    )


def check_robots_txt(
    response=None,
    robots_content=None
) -> Observation:
    """
    CR-008 — Record robots.txt evidence when supplied.

    The caller may provide robots.txt content obtained through
    an appropriate read-only web request.

    This function does not assume that a Disallow rule blocks
    every crawler.
    """

    if robots_content is None:
        return make_observation(
            "CR-008",
            "unverified",
            {
                "robots_txt_available": False
            },
            {
                "reason": (
                    "robots.txt content was not supplied to "
                    "the deterministic collector."
                )
            }
        )

    lines = [
        line.strip()
        for line in robots_content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    user_agents = []
    disallow_rules = []
    allow_rules = []

    current_agents = []

    for line in lines:
        lower = line.lower()

        if lower.startswith("user-agent:"):
            agent = line.split(":", 1)[1].strip()

            if current_agents and agent:
                current_agents.append(agent)
            else:
                current_agents = [agent]

            user_agents.append(agent)

        elif lower.startswith("disallow:"):
            rule = line.split(":", 1)[1].strip()

            disallow_rules.append({
                "user_agents": list(current_agents),
                "path": rule
            })

        elif lower.startswith("allow:"):
            rule = line.split(":", 1)[1].strip()

            allow_rules.append({
                "user_agents": list(current_agents),
                "path": rule
            })

    return make_observation(
        "CR-008",
        "pass",
        {
            "robots_txt_available": True,
            "user_agents": user_agents,
            "disallow_rules": disallow_rules,
            "allow_rules": allow_rules
        },
        {
            "interpretation": (
                "Robots rules require evaluation against the "
                "relevant crawler and requested path."
            )
        }
    )


def run_checks(
    html: str,
    response,
    robots_content=None
):
    """
    Run all crawl and rendering evidence checks.

    The implementation collects evidence. The audit agent
    determines whether observations represent material findings.
    """

    return [
        check_meta_robots_noindex(html),
        check_x_robots_noindex(response),
        check_http_access(response),
        check_empty_or_thin_html(html, response),
        check_client_side_rendering(html),
        check_missing_noscript_fallback(html),
        check_canonical(html, response),
        check_robots_txt(response, robots_content),
        check_performance_signals(html),
        check_internal_link_discovery(html, response),
    ]