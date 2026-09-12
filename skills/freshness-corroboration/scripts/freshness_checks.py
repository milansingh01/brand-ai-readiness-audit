import json
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from shared.models import Observation


DATE_PATTERN = re.compile(
    r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"
)


def extract_json_ld(html):

    soup = BeautifulSoup(html, "html.parser")

    blocks = []

    for tag in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"}
    ):
        raw = tag.string or tag.get_text()

        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    return blocks


def find_dates_in_json(data, results=None):

    if results is None:
        results = []

    if isinstance(data, dict):

        for key, value in data.items():

            if key in (
                "datePublished",
                "dateModified",
                "uploadDate"
            ):

                results.append({
                    "source": "json-ld",
                    "field": key,
                    "value": value
                })

            find_dates_in_json(value, results)

    elif isinstance(data, list):

        for item in data:
            find_dates_in_json(item, results)

    return results


def check_published_modified_dates(
    html: str,
    headers=None
) -> Observation:

    soup = BeautifulSoup(html, "html.parser")

    dates = []

    # JSON-LD dates
    for data in extract_json_ld(html):
        dates.extend(find_dates_in_json(data))

    # Visible date-like strings
    text = " ".join(soup.stripped_strings)

    visible_dates = DATE_PATTERN.findall(text)

    for year, month, day in visible_dates[:20]:

        dates.append({
            "source": "visible_text",
            "field": "date_pattern",
            "value": f"{year}-{month}-{day}"
        })

    # HTTP Last-Modified
    if headers:

        last_modified = headers.get("Last-Modified")

        if last_modified:
            dates.append({
                "source": "http_header",
                "field": "Last-Modified",
                "value": last_modified
            })

    return Observation(
        check="FC-001",
        found=len(dates) > 0,
        evidence={
            "dates": dates
        }
    )


def check_date_conflicts(html: str) -> Observation:

    blocks = extract_json_ld(html)

    published = []
    modified = []

    for data in blocks:

        entries = find_dates_in_json(data)

        for entry in entries:

            if entry["field"] == "datePublished":
                published.append(entry["value"])

            if entry["field"] == "dateModified":
                modified.append(entry["value"])

    conflicts = []

    for pub in published:

        for mod in modified:

            try:

                pub_date = datetime.fromisoformat(
                    pub.replace("Z", "+00:00")
                )

                mod_date = datetime.fromisoformat(
                    mod.replace("Z", "+00:00")
                )

                if mod_date < pub_date:

                    conflicts.append({
                        "published": pub,
                        "modified": mod
                    })

            except ValueError:
                continue

    return Observation(
        check="FC-003",
        found=len(conflicts) > 0,
        evidence={
            "conflicts": conflicts
        }
    )


def check_last_modified(headers) -> Observation:

    value = headers.get("Last-Modified")

    return Observation(
        check="FC-002",
        found=value is not None,
        evidence={
            "last_modified": value
        }
    )


def run_checks(html, headers=None, url=None):

    return [
        check_published_modified_dates(
            html,
            headers
        ),
        check_last_modified(
            headers or {}
        ),
        check_date_conflicts(html),
    ]