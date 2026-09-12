import re

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
]


def check_ctas(html: str) -> Observation:

    soup = BeautifulSoup(html, "html.parser")

    matches = []

    for element in soup.find_all(
        ["a", "button"]
    ):

        text = " ".join(element.stripped_strings)

        if not text:
            continue

        text_lower = text.lower()

        matched_words = [
            word
            for word in CTA_WORDS
            if word in text_lower
        ]

        if matched_words:

            matches.append({
                "text": text,
                "element": element.name,
                "matches": matched_words,
                "href": element.get("href")
            })

    return Observation(
        check="EA-001",
        found=len(matches) > 0,
        evidence={
            "count": len(matches),
            "ctas": matches[:50]
        }
    )


def check_navigation(html: str) -> Observation:

    soup = BeautifulSoup(html, "html.parser")

    navs = soup.find_all("nav")

    links = []

    for nav in navs:

        for link in nav.find_all("a", href=True):

            links.append({
                "text": " ".join(link.stripped_strings),
                "href": link.get("href")
            })

    return Observation(
        check="EA-002",
        found=len(links) > 0,
        evidence={
            "navigation_count": len(navs),
            "links": links[:100]
        }
    )


def check_forms(html: str) -> Observation:

    soup = BeautifulSoup(html, "html.parser")

    forms = []

    for form in soup.find_all("form"):

        fields = []

        for field in form.find_all(
            ["input", "textarea", "select"]
        ):

            fields.append({
                "name": field.get("name"),
                "type": field.get("type"),
                "placeholder": field.get("placeholder")
            })

        forms.append({
            "action": form.get("action"),
            "method": form.get("method"),
            "fields": fields
        })

    return Observation(
        check="EA-004",
        found=len(forms) > 0,
        evidence={
            "form_count": len(forms),
            "forms": forms
        }
    )


def check_headings(html: str) -> Observation:

    soup = BeautifulSoup(html, "html.parser")

    headings = []

    for level in range(1, 7):

        tag_name = f"h{level}"

        for heading in soup.find_all(tag_name):

            headings.append({
                "level": level,
                "text": " ".join(
                    heading.stripped_strings
                )
            })

    return Observation(
        check="EA-006",
        found=len(headings) > 0,
        evidence={
            "heading_count": len(headings),
            "h1_count": len(
                soup.find_all("h1")
            ),
            "headings": headings[:100]
        }
    )


def check_link_context(html: str) -> Observation:

    soup = BeautifulSoup(html, "html.parser")

    generic_labels = {
        "click here",
        "here",
        "learn more",
        "read more"
    }

    generic_links = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        text = " ".join(link.stripped_strings).strip()

        if text.lower() in generic_labels:

            generic_links.append({
                "text": text,
                "href": link.get("href")
            })

    return Observation(
        check="EA-007",
        found=len(generic_links) > 0,
        evidence={
            "generic_link_count": len(generic_links),
            "links": generic_links[:50]
        }
    )


def run_checks(html: str, url=None):

    return [
        check_ctas(html),
        check_navigation(html),
        check_forms(html),
        check_headings(html),
        check_link_context(html),
    ]