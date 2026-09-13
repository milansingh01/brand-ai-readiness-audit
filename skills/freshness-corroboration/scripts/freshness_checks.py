# skills/freshness-corroboration/scripts/freshness_checks.py
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup

from shared.models import Observation


DATE_KEYS = {
    "datePublished",
    "dateModified",
    "dateCreated",
    "uploadDate",
    "releaseDate",
    "datePosted",
    "dateUpdated",
}

TIME_SENSITIVE_SCHEMA_TYPES = {
    "Article",
    "NewsArticle",
    "BlogPosting",
    "LiveBlogPosting",
    "Event",
    "JobPosting",
    "Product",
    "Offer",
    "Course",
    "Recipe",
    "Review",
}

TIME_SENSITIVE_KEYWORDS = (
    "latest",
    "current",
    "today",
    "tomorrow",
    "yesterday",
    "news",
    "price",
    "pricing",
    "offer",
    "sale",
    "event",
    "events",
    "schedule",
    "opening hours",
    "hours",
    "availability",
    "deadline",
    "job",
    "jobs",
    "vacancy",
    "vacancies",
    "stock",
    "inventory",
    "release",
    "updated",
    "forecast",
)


def _parse_date(value: Any) -> Optional[datetime]:
    if not value:
        return None

    value = str(value).strip()

    candidates = [
        value,
        value.replace("Z", "+00:00"),
    ]

    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        return None


def _normalise_schema_type(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value.split("#")[-1].split("/")[-1]]

    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, str):
                result.append(item.split("#")[-1].split("/")[-1])
        return result

    return []


def _iter_jsonld(value: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(value, dict):
        yield value

        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _iter_jsonld(item)

    elif isinstance(value, list):
        for item in value:
            yield from _iter_jsonld(item)


def _extract_jsonld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = script.string or script.get_text()
        if not raw.strip():
            continue

        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        records.extend(_iter_jsonld(parsed))

    return records


def _extract_date_signals(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
    headers: Dict[str, str],
) -> Dict[str, List[str]]:
    signals: Dict[str, List[str]] = {
        "datePublished": [],
        "dateModified": [],
        "visible_date": [],
        "metadata_date": [],
        "last_modified": [],
    }

    for record in jsonld_records:
        for key in DATE_KEYS:
            value = record.get(key)
            if value:
                values = value if isinstance(value, list) else [value]
                for item in values:
                    if key == "datePublished":
                        signals["datePublished"].append(str(item))
                    elif key == "dateModified":
                        signals["dateModified"].append(str(item))
                    else:
                        signals["metadata_date"].append(str(item))

    for meta in soup.find_all("meta"):
        key = (
            meta.get("property")
            or meta.get("name")
            or meta.get("itemprop")
            or ""
        ).lower()

        value = meta.get("content")
        if not value:
            continue

        if any(token in key for token in ("datepublished", "article:published_time")):
            signals["datePublished"].append(value)

        if any(token in key for token in ("datemodified", "article:modified_time")):
            signals["dateModified"].append(value)

        if any(
            token in key
            for token in (
                "date",
                "published",
                "modified",
                "updated",
                "lastmod",
            )
        ):
            signals["metadata_date"].append(value)

    for element in soup.find_all("time"):
        value = element.get("datetime") or element.get_text(" ", strip=True)
        if value:
            signals["visible_date"].append(value)

    text = soup.get_text(" ", strip=True)

    date_patterns = [
        r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
    ]

    for pattern in date_patterns:
        signals["visible_date"].extend(re.findall(pattern, text, re.I))

    last_modified = headers.get("Last-Modified") or headers.get("last-modified")
    if last_modified:
        signals["last_modified"].append(last_modified)

    return signals


def _all_valid_dates(signals: Dict[str, List[str]]) -> List[datetime]:
    dates: List[datetime] = []

    for values in signals.values():
        for value in values:
            parsed = _parse_date(value)
            if parsed:
                dates.append(parsed)

    return dates


def _is_time_sensitive(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
) -> bool:
    for record in jsonld_records:
        schema_types = _normalise_schema_type(record.get("@type"))
        if any(schema_type in TIME_SENSITIVE_SCHEMA_TYPES for schema_type in schema_types):
            return True

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    headings = " ".join(
        heading.get_text(" ", strip=True)
        for heading in soup.find_all(["h1", "h2", "h3"])
    )

    sample = f"{title} {headings}".lower()

    return any(keyword in sample for keyword in TIME_SENSITIVE_KEYWORDS)


def _observation(
    check_id: str,
    check_name: str,
    status: str,
    finding: str,
    evidence: List[str],
    reasoning: str,
    severity: str = "low",
    priority: str = "low",
    suggested_action: str = "",
) -> Observation:
    return Observation(
        check_id=check_id,
        check_name=check_name,
        status=status,
        finding=finding,
        evidence=evidence,
        reasoning=reasoning,
        severity=severity,
        priority=priority,
        suggested_action=suggested_action,
    )


def check_published_date(signals: Dict[str, List[str]]) -> Observation:
    values = signals["datePublished"]

    if values:
        return _observation(
            "FC-001",
            "Published Date",
            "PASS",
            "A published-date signal is available.",
            values[:5],
            "The page exposes a publication date through structured or metadata signals.",
        )

    return _observation(
        "FC-001",
        "Published Date",
        "PASS",
        "No explicit published-date signal was found.",
        [],
        "A missing published date is not automatically an issue because not all content types require one.",
    )


def check_modified_date(signals: Dict[str, List[str]]) -> Observation:
    values = signals["dateModified"] or signals["last_modified"]

    if values:
        return _observation(
            "FC-002",
            "Modified Date",
            "PASS",
            "A modification/freshness signal is available.",
            values[:5],
            "The page exposes a modification signal through metadata, structured data, or HTTP headers.",
        )

    return _observation(
        "FC-002",
        "Modified Date",
        "PASS",
        "No explicit modified-date signal was found.",
        [],
        "A missing modified date is not automatically an issue.",
    )


def check_conflicting_dates(
    signals: Dict[str, List[str]],
) -> Observation:
    parsed: List[Tuple[str, datetime]] = []

    for category, values in signals.items():
        for value in values:
            date = _parse_date(value)
            if date:
                parsed.append((category, date))

    if len(parsed) < 2:
        return _observation(
            "FC-003",
            "Conflicting Dates",
            "UNVERIFIED",
            "There are not enough valid date signals to establish a conflict.",
            [value for values in signals.values() for value in values][:10],
            "A conflict requires multiple valid date signals that refer to the same content event.",
        )

    unique_dates = {date.date() for _, date in parsed}

    if len(unique_dates) == 1:
        return _observation(
            "FC-003",
            "Conflicting Dates",
            "PASS",
            "Available date signals are consistent.",
            [f"{category}: {date.isoformat()}" for category, date in parsed[:10]],
            "The collected date signals resolve to the same calendar date.",
        )

    return _observation(
        "FC-003",
        "Conflicting Dates",
        "ISSUE",
        "Multiple freshness signals contain materially different dates.",
        [f"{category}: {date.isoformat()}" for category, date in parsed[:10]],
        "Different dates may create uncertainty about when the content was published or updated.",
        severity="medium",
        priority="medium",
        suggested_action="Review the date sources and establish one authoritative publication or modification date.",
    )


def check_stale_content(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
    signals: Dict[str, List[str]],
    audit_time: Optional[datetime],
) -> Observation:
    if not _is_time_sensitive(soup, jsonld_records):
        return _observation(
            "FC-004",
            "Stale Content",
            "PASS",
            "The page does not appear to contain strongly time-sensitive content.",
            [],
            "Staleness should be evaluated in the context of content type and subject matter.",
        )

    dates = _all_valid_dates(signals)

    if not dates:
        return _observation(
            "FC-004",
            "Stale Content",
            "UNVERIFIED",
            "The content appears time-sensitive, but no reliable freshness date was found.",
            [],
            "Without a reliable date, the age of the content cannot be established.",
        )

    now = audit_time or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    newest = max(dates)
    age_days = (now - newest).days

    if age_days > 365:
        return _observation(
            "FC-004",
            "Stale Content",
            "ISSUE",
            f"Time-sensitive content appears to be more than {age_days} days old.",
            [f"Newest freshness signal: {newest.isoformat()}"],
            "The page appears time-sensitive and its newest available freshness signal is more than one year old.",
            severity="high",
            priority="high",
            suggested_action="Review and update the content, or clearly communicate that the information is historical.",
        )

    return _observation(
        "FC-004",
        "Stale Content",
        "PASS",
        f"The newest freshness signal is approximately {max(age_days, 0)} days old.",
        [f"Newest freshness signal: {newest.isoformat()}"],
        "The available freshness evidence does not indicate materially stale time-sensitive content.",
    )


def check_missing_freshness(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
    signals: Dict[str, List[str]],
) -> Observation:
    if not _is_time_sensitive(soup, jsonld_records):
        return _observation(
            "FC-005",
            "Missing Freshness",
            "PASS",
            "Freshness metadata is not required strongly enough to flag its absence.",
            [],
            "The page does not appear sufficiently time-sensitive to require explicit freshness metadata.",
        )

    if _all_valid_dates(signals):
        return _observation(
            "FC-005",
            "Missing Freshness",
            "PASS",
            "Freshness signals are available for the time-sensitive page.",
            [value for values in signals.values() for value in values][:10],
            "At least one usable freshness signal is present.",
        )

    return _observation(
        "FC-005",
        "Missing Freshness",
        "ISSUE",
        "Time-sensitive content has no usable freshness signal.",
        [],
        "Time-sensitive content benefits from an explicit publication or modification signal so users and systems can assess its recency.",
        severity="medium",
        priority="medium",
        suggested_action="Add an accurate published or modified date using visible content and appropriate metadata or structured data.",
    )


def check_claim_corroboration(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
) -> Observation:
    organizations: List[str] = []

    for record in jsonld_records:
        name = record.get("name")
        if isinstance(name, str) and name.strip():
            organizations.append(name.strip())

    visible_text = soup.get_text(" ", strip=True)

    if organizations:
        return _observation(
            "FC-006",
            "Claim Corroboration",
            "UNVERIFIED",
            "Important identity claims were found, but independent external corroboration was not performed by this collector.",
            organizations[:10],
            "External corroboration requires independent web sources and cannot be established from the page alone.",
        )

    if visible_text:
        return _observation(
            "FC-006",
            "Claim Corroboration",
            "UNVERIFIED",
            "The page contains claims, but independent external corroboration was not performed by this collector.",
            [],
            "External corroboration requires independent sources.",
        )

    return _observation(
        "FC-006",
        "Claim Corroboration",
        "UNVERIFIED",
        "No usable page content was available for corroboration.",
        [],
        "Independent corroboration cannot be assessed without accessible content and external sources.",
    )


def check_contradictory_information(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
) -> Observation:
    names: List[str] = []

    for record in jsonld_records:
        name = record.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())

    unique_names = list(dict.fromkeys(names))

    if len(unique_names) <= 1:
        return _observation(
            "FC-007",
            "Contradictory Information",
            "PASS",
            "No material contradiction was detected in the available structured identity signals.",
            unique_names,
            "Only one consistent structured identity name was found.",
        )

    return _observation(
        "FC-007",
        "Contradictory Information",
        "ISSUE",
        "Multiple structured identity names were detected on the same page.",
        unique_names[:10],
        "Multiple organization/entity names may indicate inconsistent identity information and should be reviewed.",
        severity="medium",
        priority="medium",
        suggested_action="Review structured data and page content so the primary entity is represented consistently.",
    )


def check_entity_identity(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
    url: Optional[str],
) -> Observation:
    signals: List[str] = []

    for record in jsonld_records:
        schema_types = _normalise_schema_type(record.get("@type"))

        if schema_types:
            signals.extend(f"schema_type={item}" for item in schema_types)

        if record.get("name"):
            signals.append(f"name={record['name']}")

        if record.get("sameAs"):
            values = record["sameAs"]
            if isinstance(values, str):
                values = [values]
            signals.extend(f"sameAs={value}" for value in values)

        for identifier_key in ("identifier", "url"):
            if record.get(identifier_key):
                signals.append(f"{identifier_key}={record[identifier_key]}")

    page_text = soup.get_text(" ", strip=True).lower()

    if soup.find(["address"]):
        signals.append("address_element")

    if "about" in page_text:
        signals.append("about_signal")

    if "contact" in page_text:
        signals.append("contact_signal")

    if url:
        signals.append(f"domain={url}")

    if len(signals) >= 2:
        return _observation(
            "FC-008",
            "Entity Identity",
            "PASS",
            "The page provides multiple entity identity signals.",
            signals[:15],
            "Multiple independent identity signals provide reasonable evidence of the represented entity.",
        )

    return _observation(
        "FC-008",
        "Entity Identity",
        "UNVERIFIED",
        "Insufficient identity signals were available to confidently assess entity identity.",
        signals,
        "The collector did not find enough independent identity signals to establish or reject identity confidence.",
    )


def check_entity_disambiguation(
    soup: BeautifulSoup,
    jsonld_records: List[Dict[str, Any]],
    url: Optional[str],
) -> Observation:
    signals: List[str] = []

    for record in jsonld_records:
        if record.get("sameAs"):
            values = record["sameAs"]
            if isinstance(values, str):
                values = [values]
            signals.extend(f"sameAs={value}" for value in values)

        if record.get("identifier"):
            signals.append(f"identifier={record['identifier']}")

        schema_types = _normalise_schema_type(record.get("@type"))
        signals.extend(f"type={value}" for value in schema_types)

        if record.get("name"):
            signals.append(f"name={record['name']}")

    if url:
        signals.append(f"official_domain={url}")

    if soup.find("address"):
        signals.append("address")

    if soup.find("a", href=re.compile(r"/(?:about|contact)(?:/|$)", re.I)):
        signals.append("about_or_contact_link")

    unique_signals = list(dict.fromkeys(signals))

    if len(unique_signals) >= 2:
        return _observation(
            "FC-009",
            "Entity Disambiguation",
            "PASS",
            "Multiple signals help distinguish the entity from similarly named entities.",
            unique_signals[:15],
            "The page provides several entity-specific signals that improve disambiguation.",
        )

    return _observation(
        "FC-009",
        "Entity Disambiguation",
        "UNVERIFIED",
        "Not enough entity-specific signals were available to confidently assess disambiguation.",
        unique_signals,
        "Absence of strong disambiguation signals is not sufficient by itself to establish an ambiguity issue.",
    )


def run_checks(
    html: str,
    headers: Optional[Dict[str, str]] = None,
    url: Optional[str] = None,
    audit_time: Optional[datetime] = None,
) -> List[Observation]:
    headers = headers or {}

    soup = BeautifulSoup(html or "", "html.parser")
    jsonld_records = _extract_jsonld(soup)
    signals = _extract_date_signals(soup, jsonld_records, headers)

    return [
        check_published_date(signals),
        check_modified_date(signals),
        check_conflicting_dates(signals),
        check_stale_content(
            soup,
            jsonld_records,
            signals,
            audit_time,
        ),
        check_missing_freshness(
            soup,
            jsonld_records,
            signals,
        ),
        check_claim_corroboration(
            soup,
            jsonld_records,
        ),
        check_contradictory_information(
            soup,
            jsonld_records,
        ),
        check_entity_identity(
            soup,
            jsonld_records,
            url,
        ),
        check_entity_disambiguation(
            soup,
            jsonld_records,
            url,
        ),
    ]