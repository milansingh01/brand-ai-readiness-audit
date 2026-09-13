import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from shared.models import Observation


CTA_WORDS = [
    "buy",
    "shop",
    "book",
    "contact",
    "sign up",
    "signup",
    "get started",
    "learn more",
    "apply",
    "request demo",
    "subscribe",
    "donate",
    "download",
    "order",
    "reserve",
    "schedule",
    "start now",
]

GENERIC_LINK_LABELS = {
    "click here",
    "here",
    "learn more",
    "read more",
    "more",
    "details",
}

CONTACT_PATTERNS = {
    "email": re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    ),
    "phone": re.compile(
        r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
    ),
}

SEMANTIC_TAGS = [
    "header",
    "nav",
    "main",
    "article",
    "section",
    "aside",
    "footer",
]

INTERACTION_ATTRIBUTES = [
    "data-toggle",
    "data-bs-toggle",
    "data-tab",
    "data-accordion",
    "data-collapsed",
    "aria-expanded",
]

HIDDEN_STYLE_PATTERN = re.compile(
    r"(?i)(display\s*:\s*none|visibility\s*:\s*hidden|"
    r"opacity\s*:\s*0|max-height\s*:\s*0)"
)


def _text(element):
    return " ".join(element.stripped_strings).strip()


def _is_hidden(element):
    if element.has_attr("hidden"):
        return True

    if element.get("aria-hidden", "").lower() == "true":
        return True

    style = element.get("style", "")
    if HIDDEN_STYLE_PATTERN.search(style):
        return True

    classes = {
        str(value).lower()
        for value in element.get("class", [])
    }

    hidden_class_names = {
        "hidden",
        "is-hidden",
        "visually-hidden",
        "sr-only",
        "d-none",
        "display-none",
    }

    return bool(classes.intersection(hidden_class_names))


def _requires_interaction(element):
    if any(element.has_attr(attribute) for attribute in INTERACTION_ATTRIBUTES):
        return True

    if element.name in {"details", "dialog"}:
        return True

    classes = " ".join(element.get("class", [])).lower()
    interaction_terms = [
        "accordion",
        "collapse",
        "tab-panel",
        "tabpanel",
        "modal",
        "drawer",
        "dropdown",
        "toggle",
        "expand",
    ]

    return any(term in classes for term in interaction_terms)


def _absolute_url(url, href):
    if not href:
        return None

    try:
        return urljoin(url or "", href)
    except Exception:
        return href


def _same_site(url, target):
    if not target:
        return False

    source_host = urlparse(url or "").netloc.lower()
    target_host = urlparse(target).netloc.lower()

    if not source_host or not target_host:
        return target.startswith("/") or target.startswith("#")

    return source_host == target_host or target_host.endswith(
        "." + source_host
    )


def check_ctas(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    matches = []

    for element in soup.find_all(["a", "button", "input"]):
        if element.name == "input":
            input_type = element.get("type", "text").lower()
            if input_type not in {"button", "submit", "image"}:
                continue
            text = element.get("value", "")
        else:
            text = _text(element)

        if not text:
            continue

        lowered = text.lower()
        matched_words = [
            word for word in CTA_WORDS if word in lowered
        ]

        if matched_words:
            matches.append(
                {
                    "text": text,
                    "element": element.name,
                    "matches": matched_words,
                    "href": _absolute_url(url, element.get("href")),
                    "type": element.get("type"),
                }
            )

    return Observation(
        check="EA-001",
        found=len(matches) > 0,
        evidence={
            "count": len(matches),
            "ctas": matches[:50],
        },
    )


def check_navigation(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    navs = soup.find_all("nav")
    links = []

    for nav in navs:
        for link in nav.find_all("a", href=True):
            links.append(
                {
                    "text": _text(link),
                    "href": _absolute_url(url, link.get("href")),
                    "aria_label": link.get("aria-label"),
                }
            )

    return Observation(
        check="EA-002",
        found=len(links) > 0,
        evidence={
            "navigation_count": len(navs),
            "links": links[:100],
            "important_sections_reachable_from_nav": bool(links),
        },
    )


def check_hidden_content(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    hidden_elements = []

    for element in soup.find_all(True):
        if not (_is_hidden(element) or _requires_interaction(element)):
            continue

        text = _text(element)
        if not text:
            continue

        hidden_elements.append(
            {
                "element": element.name,
                "text": text[:500],
                "hidden": _is_hidden(element),
                "interaction_required": _requires_interaction(element),
                "aria_hidden": element.get("aria-hidden"),
                "class": element.get("class", []),
            }
        )

    return Observation(
        check="EA-003",
        found=len(hidden_elements) > 0,
        evidence={
            "count": len(hidden_elements),
            "elements": hidden_elements[:100],
            "interpretation": (
                "These are possible hidden or interaction-dependent "
                "content areas. Presence alone is not a defect."
            ),
        },
    )


def check_forms(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    forms = []

    for form in soup.find_all("form"):
        fields = []

        for field in form.find_all(
            ["input", "textarea", "select"]
        ):
            field_id = field.get("id")
            associated_label = None

            if field_id:
                label = soup.find("label", attrs={"for": field_id})
                if label:
                    associated_label = _text(label)

            fields.append(
                {
                    "name": field.get("name"),
                    "id": field_id,
                    "type": field.get("type"),
                    "placeholder": field.get("placeholder"),
                    "label": associated_label,
                    "required": field.has_attr("required"),
                }
            )

        forms.append(
            {
                "action": _absolute_url(url, form.get("action")),
                "method": form.get("method", "get").lower(),
                "fields": fields,
            }
        )

    return Observation(
        check="EA-004",
        found=len(forms) > 0,
        evidence={
            "form_count": len(forms),
            "forms": forms[:50],
        },
    )


def check_contact_conversion(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    emails = sorted(set(CONTACT_PATTERNS["email"].findall(page_text)))
    phones = sorted(set(CONTACT_PATTERNS["phone"].findall(page_text)))

    contact_links = []
    booking_links = []
    inquiry_forms = []

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        text = _text(link)
        lowered_href = href.lower()
        lowered_text = text.lower()

        item = {
            "text": text,
            "href": _absolute_url(url, href),
        }

        if (
            lowered_href.startswith("mailto:")
            or "contact" in lowered_text
            or "contact" in lowered_href
        ):
            contact_links.append(item)

        if any(
            term in lowered_text or term in lowered_href
            for term in ["book", "booking", "reserve", "reservation", "schedule"]
        ):
            booking_links.append(item)

    for form in soup.find_all("form"):
        form_text = _text(form).lower()
        field_names = " ".join(
            field.get("name", "")
            for field in form.find_all(
                ["input", "textarea", "select"]
            )
        ).lower()

        if any(
            term in form_text or term in field_names
            for term in ["contact", "inquiry", "enquiry", "message", "email"]
        ):
            inquiry_forms.append(
                {
                    "action": _absolute_url(url, form.get("action")),
                    "fields": len(
                        form.find_all(["input", "textarea", "select"])
                    ),
                }
            )

    return Observation(
        check="EA-005",
        found=bool(
            emails
            or phones
            or contact_links
            or booking_links
            or inquiry_forms
        ),
        evidence={
            "emails": emails[:50],
            "phones": phones[:50],
            "contact_links": contact_links[:50],
            "booking_links": booking_links[:50],
            "inquiry_forms": inquiry_forms[:50],
        },
    )


def check_headings(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    headings = []

    for heading in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6"]
    ):
        level = int(heading.name[1:])
        headings.append(
            {
                "level": level,
                "text": _text(heading),
            }
        )

    hierarchy_gaps = []

    for previous, current in zip(headings, headings[1:]):
        if current["level"] > previous["level"] + 1:
            hierarchy_gaps.append(
                {
                    "from": previous,
                    "to": current,
                }
            )

    return Observation(
        check="EA-006",
        found=len(headings) > 0,
        evidence={
            "heading_count": len(headings),
            "h1_count": len(soup.find_all("h1")),
            "headings": headings[:100],
            "hierarchy_gaps": hierarchy_gaps[:50],
        },
    )


def check_link_context(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    generic_links = []

    for link in soup.find_all("a", href=True):
        text = _text(link)

        if text.lower() in GENERIC_LINK_LABELS:
            generic_links.append(
                {
                    "text": text,
                    "href": _absolute_url(url, link.get("href")),
                }
            )

    return Observation(
        check="EA-007",
        found=len(generic_links) > 0,
        evidence={
            "generic_link_count": len(generic_links),
            "links": generic_links[:50],
        },
    )


def check_friction(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    friction_signals = []

    for element in soup.find_all(["a", "button"]):
        text = _text(element)
        href = element.get("href")

        if element.name == "button" and not text:
            friction_signals.append(
                {
                    "type": "empty_button",
                    "element": "button",
                }
            )

        if element.name == "a" and not text:
            friction_signals.append(
                {
                    "type": "empty_link",
                    "href": _absolute_url(url, href),
                }
            )

        if text.lower() in GENERIC_LINK_LABELS:
            friction_signals.append(
                {
                    "type": "unclear_link_label",
                    "text": text,
                    "href": _absolute_url(url, href),
                }
            )

    for element in soup.find_all(True):
        if _requires_interaction(element) and _text(element):
            friction_signals.append(
                {
                    "type": "interaction_dependent_content",
                    "element": element.name,
                    "text": _text(element)[:300],
                }
            )

    return Observation(
        check="EA-008",
        found=len(friction_signals) > 0,
        evidence={
            "count": len(friction_signals),
            "signals": friction_signals[:100],
            "interpretation": (
                "These are possible friction signals and require "
                "contextual review before assigning severity."
            ),
        },
    )


def check_image_alt(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    images = []
    missing_alt = []

    for image in soup.find_all("img"):
        alt = image.get("alt")
        role = image.get("role", "")
        classes = " ".join(image.get("class", [])).lower()

        decorative = (
            alt == ""
            or role == "presentation"
            or role == "none"
            or "decorative" in classes
        )

        item = {
            "src": image.get("src") or image.get("data-src"),
            "alt": alt,
            "decorative_candidate": decorative,
        }

        images.append(item)

        if alt is None and not decorative:
            missing_alt.append(item)

    return Observation(
        check="EA-009",
        found=len(missing_alt) > 0,
        evidence={
            "image_count": len(images),
            "missing_alt_count": len(missing_alt),
            "missing_alt_images": missing_alt[:100],
            "interpretation": (
                "Decorative images are not treated as missing-alt defects."
            ),
        },
    )


def check_lazy_loaded_content(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    lazy_elements = []

    for element in soup.find_all(True):
        attributes = " ".join(
            f"{key}={value}"
            for key, value in element.attrs.items()
        ).lower()

        if (
            element.get("loading") == "lazy"
            or "data-src" in element.attrs
            or "data-lazy" in element.attrs
            or "intersectionobserver" in attributes
            or "lazy" in attributes
        ):
            lazy_elements.append(
                {
                    "element": element.name,
                    "text": _text(element)[:300],
                    "attributes": {
                        key: value
                        for key, value in element.attrs.items()
                        if "lazy" in key.lower()
                        or key in {"loading", "src", "data-src"}
                    },
                }
            )

    return Observation(
        check="EA-010",
        found=len(lazy_elements) > 0,
        evidence={
            "count": len(lazy_elements),
            "elements": lazy_elements[:100],
            "interpretation": (
                "Lazy-loading presence is observational only. "
                "It is not a defect unless important content fails "
                "to load reliably or requires unnecessary interaction."
            ),
        },
    )


def check_iframes(html: str, url=None) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    frames = []

    for frame in soup.find_all("iframe"):
        frames.append(
            {
                "src": _absolute_url(url, frame.get("src")),
                "title": frame.get("title"),
                "width": frame.get("width"),
                "height": frame.get("height"),
                "text": _text(frame)[:300],
            }
        )

    return Observation(
        check="EA-011",
        found=len(frames) > 0,
        evidence={
            "iframe_count": len(frames),
            "iframes": frames[:100],
            "interpretation": (
                "Iframe presence alone is not a defect. "
                "Review whether embedded important content is accessible."
            ),
        },
    )


def check_semantic_html(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    counts = {
        tag: len(soup.find_all(tag))
        for tag in SEMANTIC_TAGS
    }

    return Observation(
        check="EA-012",
        found=sum(counts.values()) > 0,
        evidence={
            "semantic_tag_counts": counts,
            "semantic_tag_total": sum(counts.values()),
            "interpretation": (
                "Semantic tag counts are supporting evidence only "
                "and do not automatically indicate an engagement defect."
            ),
        },
    )


def check_above_fold_clarity(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    first_heading = soup.find(["h1", "h2"])
    first_cta = None

    for element in soup.find_all(["a", "button"]):
        text = _text(element).lower()
        if text and any(word in text for word in CTA_WORDS):
            first_cta = {
                "text": _text(element),
                "element": element.name,
            }
            break

    return Observation(
        check="EA-013",
        found=bool(first_heading or first_cta),
        evidence={
            "first_heading": _text(first_heading)
            if first_heading
            else None,
            "first_cta": first_cta,
            "visual_above_fold_verified": False,
            "interpretation": (
                "Raw HTML cannot establish precise above-fold layout "
                "or visual clarity."
            ),
        },
    )


def check_mobile_signals(html: str) -> Observation:
    soup = BeautifulSoup(html, "html.parser")
    viewport = soup.find(
        "meta",
        attrs={"name": re.compile(r"^viewport$", re.IGNORECASE)},
    )

    responsive_signals = {
        "viewport_meta": viewport.get("content")
        if viewport
        else None,
        "media_queries_in_style": bool(
            re.search(r"@media\b", html, re.IGNORECASE)
        ),
        "responsive_class_signals": bool(
            re.search(
                r"\b(container-fluid|col-\w+|responsive|flex|grid)\b",
                html,
                re.IGNORECASE,
            )
        ),
    }

    return Observation(
        check="EA-014",
        found=bool(
            responsive_signals["viewport_meta"]
            or responsive_signals["media_queries_in_style"]
            or responsive_signals["responsive_class_signals"]
        ),
        evidence={
            **responsive_signals,
            "interpretation": (
                "These are available responsive signals. "
                "HTML inspection alone cannot prove mobile usability."
            ),
        },
    )


def run_checks(html: str, url=None):
    return [
        check_ctas(html, url),
        check_navigation(html, url),
        check_hidden_content(html),
        check_forms(html, url),
        check_contact_conversion(html, url),
        check_headings(html),
        check_link_context(html, url),
        check_friction(html, url),
        check_image_alt(html),
        check_lazy_loaded_content(html),
        check_iframes(html, url),
        check_semantic_html(html),
        check_above_fold_clarity(html),
        check_mobile_signals(html),
    ]