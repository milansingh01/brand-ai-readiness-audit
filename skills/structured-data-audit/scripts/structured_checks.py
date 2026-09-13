import json
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup

from shared.models import Observation


SUPPORTED_SCHEMA_PROPERTIES = {
    "Product": ["name", "description", "image", "offers"],
    "Article": ["headline", "author", "datePublished", "dateModified"],
    "NewsArticle": ["headline", "author", "datePublished", "dateModified"],
    "ReportageNewsArticle": [
        "headline",
        "author",
        "datePublished",
        "dateModified",
    ],
    "Organization": ["name", "url", "logo"],
    "NewsMediaOrganization": ["name", "url", "logo"],
    "LocalBusiness": ["name", "address", "telephone", "url"],
    "FAQPage": ["mainEntity"],
    "BreadcrumbList": ["itemListElement"],
}


def _observation(
    check: str,
    status: str,
    evidence: Any,
    details: Optional[Dict[str, Any]] = None,
) -> Observation:
    """
    Keep compatibility with the existing Observation model while adding
    explicit status information required by the skill guidance.

    `found` means that an issue or notable condition was detected.
    """
    if details is None:
        details = {}

    issue_statuses = {"issue", "error"}

    return Observation(
        check=check,
        found=status in issue_statuses,
        evidence={
            "status": status,
            "details": details,
            "data": evidence,
        },
    )


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html or "", "html.parser")


def extract_json_ld(html: str) -> List[str]:
    soup = get_soup(html)
    blocks = []

    for tag in soup.find_all(
        "script",
        attrs={"type": re.compile(r"^application/ld\+json$", re.I)},
    ):
        raw = tag.string or tag.get_text()
        raw = raw.strip()

        if raw:
            blocks.append(raw)

    return blocks


def parse_json_ld(html: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Return valid and invalid JSON-LD blocks.

    Valid entries contain:
      - index
      - raw
      - data

    Invalid entries contain:
      - index
      - raw
      - error
    """
    valid = []
    invalid = []

    for index, raw in enumerate(extract_json_ld(html)):
        try:
            data = json.loads(raw)

            valid.append(
                {
                    "index": index,
                    "raw": raw,
                    "data": data,
                }
            )
        except json.JSONDecodeError as error:
            invalid.append(
                {
                    "index": index,
                    "raw": raw,
                    "error": str(error),
                }
            )

    return valid, invalid


def _iter_dicts(value: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from _iter_dicts(child)

    elif isinstance(value, list):
        for item in value:
            yield from _iter_dicts(item)


def extract_schema_types(data: Any) -> List[str]:
    types = []

    for item in _iter_dicts(data):
        value = item.get("@type")

        if isinstance(value, list):
            types.extend(str(item_type) for item_type in value)
        elif value:
            types.append(str(value))

    return sorted(set(types))


def extract_schema_entities(data: Any) -> List[Dict[str, Any]]:
    """
    Extract dictionaries that contain an @type value.

    This supports JSON-LD objects nested inside @graph arrays.
    """
    entities = []

    for item in _iter_dicts(data):
        if "@type" in item:
            entities.append(item)

    return entities


def _first_non_empty(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, list):
        for item in value:
            result = _first_non_empty(item)
            if result:
                return result
        return None

    if isinstance(value, dict):
        for key in ("name", "headline", "text", "@id", "url"):
            result = _first_non_empty(value.get(key))
            if result:
                return result
        return None

    text = str(value).strip()
    return text or None


def _normalise_text(value: Any) -> str:
    text = _first_non_empty(value) or ""
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _visible_text(soup: BeautifulSoup) -> str:
    for element in soup(
        ["script", "style", "noscript", "template", "svg"]
    ):
        element.decompose()

    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def _page_title(soup: BeautifulSoup) -> str:
    title = soup.find("title")
    return title.get_text(" ", strip=True) if title else ""


def _headings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    headings = []

    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        text = heading.get_text(" ", strip=True)

        headings.append(
            {
                "level": int(heading.name[1]),
                "text": text,
            }
        )

    return headings


def _meta_content(soup: BeautifulSoup, **attrs: str) -> Optional[str]:
    tag = soup.find("meta", attrs=attrs)

    if not tag:
        return None

    content = tag.get("content")
    return content.strip() if isinstance(content, str) else None


def _link_href(soup: BeautifulSoup, **attrs: str) -> Optional[str]:
    tag = soup.find("link", attrs=attrs)

    if not tag:
        return None

    href = tag.get("href")
    return href.strip() if isinstance(href, str) else None


def _schema_type_matches(entity: Dict[str, Any], expected: str) -> bool:
    value = entity.get("@type")

    if isinstance(value, list):
        return expected in value

    return value == expected


def _entity_label(entity: Dict[str, Any]) -> str:
    for key in ("name", "headline", "url", "@id"):
        value = _first_non_empty(entity.get(key))
        if value:
            return value

    return ""


def _entity_key(entity: Dict[str, Any]) -> str:
    """
    Prefer stable identity fields when available. Fall back to type plus
    name/headline so repeated entities can be compared.
    """
    entity_type = _first_non_empty(entity.get("@type")) or "Unknown"
    identity = (
        _first_non_empty(entity.get("@id"))
        or _first_non_empty(entity.get("url"))
        or _first_non_empty(entity.get("name"))
        or _first_non_empty(entity.get("headline"))
        or ""
    )

    return f"{entity_type}:{_normalise_text(identity)}"


def check_structured_data_presence(html: str) -> Observation:
    blocks = extract_json_ld(html)

    return _observation(
        check="SD-001",
        status="pass" if blocks else "unverified",
        evidence={
            "formats": ["application/ld+json"] if blocks else [],
            "json_ld_blocks": len(blocks),
        },
        details={
            "interpretation": (
                "JSON-LD is present."
                if blocks
                else (
                    "No JSON-LD was detected. This is not automatically a defect; "
                    "page purpose and other machine-readable signals must be considered."
                )
            ),
            "impact": "informational",
            "scope": "page",
        },
    )


def check_json_ld_validity(html: str) -> Observation:
    valid, invalid = parse_json_ld(html)

    if invalid:
        status = "issue"
    elif valid:
        status = "pass"
    else:
        status = "unverified"

    return _observation(
        check="SD-002",
        status=status,
        evidence={
            "total": len(valid) + len(invalid),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "valid": [
                {
                    "index": item["index"],
                    "json_type": type(item["data"]).__name__,
                }
                for item in valid
            ],
            "invalid": [
                {
                    "index": item["index"],
                    "error": item["error"],
                }
                for item in invalid
            ],
        },
        details={
            "impact": "high" if invalid else "informational",
            "scope": "page",
        },
    )


def check_schema_types(html: str) -> Observation:
    valid, _ = parse_json_ld(html)
    types = []

    for item in valid:
        types.extend(extract_schema_types(item["data"]))

    types = sorted(set(types))

    return _observation(
        check="SD-003",
        status="pass" if types else "unverified",
        evidence={
            "types": types,
            "type_count": len(types),
        },
        details={
            "impact": "informational",
            "scope": "page",
        },
    )


def check_schema_properties(html: str) -> Observation:
    valid, _ = parse_json_ld(html)
    results = []

    for block in valid:
        entities = extract_schema_entities(block["data"])

        for entity_index, entity in enumerate(entities):
            schema_types = entity.get("@type")

            if isinstance(schema_types, str):
                schema_types = [schema_types]
            elif not isinstance(schema_types, list):
                schema_types = []

            for schema_type in schema_types:
                properties = SUPPORTED_SCHEMA_PROPERTIES.get(schema_type)

                if not properties:
                    continue

                results.append(
                    {
                        "block_index": block["index"],
                        "entity_index": entity_index,
                        "type": schema_type,
                        "present": {
                            prop: bool(entity.get(prop))
                            for prop in properties
                        },
                    }
                )

    missing_important_properties = [
        {
            **result,
            "missing": [
                prop
                for prop, present in result["present"].items()
                if not present
            ],
        }
        for result in results
        if any(not present for present in result["present"].values())
    ]

    status = "issue" if missing_important_properties else (
        "pass" if results else "unverified"
    )

    return _observation(
        check="SD-004",
        status=status,
        evidence={
            "recognized_entities": results,
            "entities_with_missing_properties": missing_important_properties,
        },
        details={
            "interpretation": (
                "Presence/absence is reported only. Missing properties require "
                "contextual interpretation based on page type and importance."
            ),
            "impact": "medium" if missing_important_properties else "informational",
            "scope": "page",
        },
    )


def check_schema_consistency(html: str) -> Observation:
    soup = get_soup(html)
    visible_text = _normalise_text(_visible_text(soup))
    page_title = _normalise_text(_page_title(soup))

    valid, _ = parse_json_ld(html)
    comparisons = []

    for block in valid:
        for entity in extract_schema_entities(block["data"]):
            schema_type = _first_non_empty(entity.get("@type")) or "Unknown"

            candidates = []

            for property_name in ("name", "headline", "description"):
                value = _first_non_empty(entity.get(property_name))

                if value:
                    candidates.append(
                        {
                            "property": property_name,
                            "value": value,
                        }
                    )

            for candidate in candidates:
                value = _normalise_text(candidate["value"])

                if not value:
                    continue

                in_title = value in page_title if page_title else False
                in_visible_text = value in visible_text if visible_text else False

                comparisons.append(
                    {
                        "type": schema_type,
                        "property": candidate["property"],
                        "value": candidate["value"],
                        "found_in_title": in_title,
                        "found_in_visible_text": in_visible_text,
                        "match": in_title or in_visible_text,
                    }
                )

    mismatches = [
        item
        for item in comparisons
        if not item["match"]
    ]

    return _observation(
        check="SD-005",
        status="issue" if mismatches else (
            "pass" if comparisons else "unverified"
        ),
        evidence={
            "comparisons": comparisons,
            "potential_mismatches": mismatches,
        },
        details={
            "interpretation": (
                "A mismatch is only a signal for review. Some structured values "
                "may legitimately not appear verbatim in visible page text."
            ),
            "impact": "medium" if mismatches else "informational",
            "scope": "page",
        },
    )


def check_duplicate_or_conflicting_schema(html: str) -> Observation:
    valid, _ = parse_json_ld(html)
    entities_by_key = defaultdict(list)

    for block in valid:
        for entity in extract_schema_entities(block["data"]):
            entities_by_key[_entity_key(entity)].append(entity)

    duplicate_entities = []
    conflicts = []

    comparison_properties = (
        "name",
        "headline",
        "url",
        "description",
        "datePublished",
        "dateModified",
        "price",
        "priceCurrency",
    )

    for key, entities in entities_by_key.items():
        if len(entities) < 2:
            continue

        duplicate_entities.append(
            {
                "entity_key": key,
                "count": len(entities),
                "types": [
                    _first_non_empty(entity.get("@type"))
                    for entity in entities
                ],
            }
        )

        for property_name in comparison_properties:
            values = {
                _normalise_text(entity.get(property_name))
                for entity in entities
                if _normalise_text(entity.get(property_name))
            }

            if len(values) > 1:
                conflicts.append(
                    {
                        "entity_key": key,
                        "property": property_name,
                        "values": sorted(values),
                    }
                )

    status = "issue" if conflicts else (
        "pass" if duplicate_entities else "unverified"
    )

    return _observation(
        check="SD-006",
        status=status,
        evidence={
            "duplicate_entities": duplicate_entities,
            "conflicts": conflicts,
        },
        details={
            "impact": "high" if conflicts else "informational",
            "scope": "page",
        },
    )


def check_breadcrumb_structure(html: str) -> Observation:
    valid, _ = parse_json_ld(html)
    breadcrumb_entities = []

    for block in valid:
        for entity in extract_schema_entities(block["data"]):
            if _schema_type_matches(entity, "BreadcrumbList"):
                items = entity.get("itemListElement")

                if not isinstance(items, list):
                    items = []

                breadcrumb_entities.append(
                    {
                        "item_count": len(items),
                        "items": items,
                    }
                )

    return _observation(
        check="SD-007",
        status="pass" if breadcrumb_entities else "unverified",
        evidence={
            "present": bool(breadcrumb_entities),
            "breadcrumb_lists": breadcrumb_entities,
        },
        details={
            "interpretation": (
                "Breadcrumbs are reported when present. Their absence is not "
                "automatically a defect because appropriateness depends on page type."
            ),
            "impact": "informational",
            "scope": "page",
        },
    )


def check_heading_structure(html: str) -> Observation:
    soup = get_soup(html)
    headings = _headings(soup)

    h1_count = sum(item["level"] == 1 for item in headings)
    meaningful_headings = [
        item for item in headings if item["text"].strip()
    ]

    skipped_levels = []

    previous_level = None

    for heading in meaningful_headings:
        level = heading["level"]

        if previous_level is not None and level > previous_level + 1:
            skipped_levels.append(
                {
                    "from": previous_level,
                    "to": level,
                    "text": heading["text"],
                }
            )

        previous_level = level

    issue = bool(skipped_levels)

    if not headings:
        status = "unverified"
    elif issue:
        status = "issue"
    else:
        status = "pass"

    return _observation(
        check="SD-008",
        status=status,
        evidence={
            "heading_count": len(headings),
            "h1_count": h1_count,
            "headings": headings,
            "skipped_levels": skipped_levels,
        },
        details={
            "interpretation": (
                "Heading quality is assessed from hierarchy and meaningful "
                "content, not from an exact one-H1 rule."
            ),
            "impact": "low" if issue else "informational",
            "scope": "page",
        },
    )


def check_meta_description(html: str) -> Observation:
    soup = get_soup(html)
    description = _meta_content(soup, attrs={"name": re.compile(r"^description$", re.I)})

    if description:
        status = "pass"
    else:
        status = "unverified"

    return _observation(
        check="SD-009",
        status=status,
        evidence={
            "present": bool(description),
            "length": len(description) if description else 0,
            "description": description,
        },
        details={
            "interpretation": (
                "A missing description is not treated as a major AI "
                "discoverability failure by itself."
            ),
            "impact": "low" if not description else "informational",
            "scope": "page",
        },
    )


def _collect_meta_properties(
    soup: BeautifulSoup,
    prefix: str,
) -> Dict[str, str]:
    result = {}

    for tag in soup.find_all("meta"):
        property_name = tag.get("property") or tag.get("name")

        if not isinstance(property_name, str):
            continue

        if property_name.lower().startswith(prefix.lower()):
            content = tag.get("content")

            if isinstance(content, str) and content.strip():
                result[property_name.lower()] = content.strip()

    return result


def check_open_graph_metadata(html: str) -> Observation:
    soup = get_soup(html)
    metadata = _collect_meta_properties(soup, "og:")

    relevant = {
        key: metadata.get(key)
        for key in (
            "og:title",
            "og:description",
            "og:image",
            "og:url",
        )
    }

    present_count = sum(bool(value) for value in relevant.values())

    return _observation(
        check="SD-010",
        status="pass" if present_count else "unverified",
        evidence={
            "metadata": relevant,
            "present_count": present_count,
            "expected_supporting_fields": list(relevant.keys()),
        },
        details={
            "interpretation": (
                "Open Graph is supporting preview metadata, not a mandatory "
                "AI-discoverability requirement."
            ),
            "impact": "low" if 0 < present_count < len(relevant) else "informational",
            "scope": "page",
        },
    )


def check_twitter_metadata(html: str) -> Observation:
    soup = get_soup(html)
    metadata = _collect_meta_properties(soup, "twitter:")

    relevant = {
        key: metadata.get(key)
        for key in (
            "twitter:card",
            "twitter:title",
            "twitter:description",
            "twitter:image",
        )
    }

    present_count = sum(bool(value) for value in relevant.values())

    return _observation(
        check="SD-011",
        status="pass" if present_count else "unverified",
        evidence={
            "metadata": relevant,
            "present_count": present_count,
            "expected_supporting_fields": list(relevant.keys()),
        },
        details={
            "interpretation": (
                "Twitter Card metadata is optional supporting metadata and is "
                "not required for AI extraction."
            ),
            "impact": "low" if 0 < present_count < len(relevant) else "informational",
            "scope": "page",
        },
    )


def check_image_alt_text(html: str) -> Observation:
    soup = get_soup(html)
    images = soup.find_all("img")

    image_results = []
    missing_alt = []

    for index, image in enumerate(images):
        alt = image.get("alt")
        src = image.get("src") or image.get("data-src") or image.get("data-lazy-src")

        role = (image.get("role") or "").lower()
        aria_hidden = str(image.get("aria-hidden") or "").lower() == "true"
        is_decorative = role == "presentation" or aria_hidden or alt == ""

        result = {
            "index": index,
            "src": src,
            "has_alt_attribute": alt is not None,
            "alt": alt,
            "likely_decorative": is_decorative,
        }

        image_results.append(result)

        if alt is None and not is_decorative:
            missing_alt.append(result)

    return _observation(
        check="SD-012",
        status="issue" if missing_alt else (
            "pass" if images else "unverified"
        ),
        evidence={
            "total_images": len(images),
            "images_with_alt": sum(
                item["has_alt_attribute"] for item in image_results
            ),
            "missing_alt_on_likely_informational_images": missing_alt,
            "images": image_results,
        },
        details={
            "interpretation": (
                "Decorative images are not treated as requiring descriptive "
                "alternative text. Image purpose may require manual review."
            ),
            "impact": "medium" if missing_alt else "informational",
            "scope": "page",
        },
    )


def check_semantic_html(html: str) -> Observation:
    soup = get_soup(html)

    semantic_elements = (
        "header",
        "nav",
        "main",
        "article",
        "section",
        "footer",
    )

    counts = {
        element: len(soup.find_all(element))
        for element in semantic_elements
    }

    present = [
        element
        for element, count in counts.items()
        if count > 0
    ]

    return _observation(
        check="SD-013",
        status="pass" if present else "unverified",
        evidence={
            "counts": counts,
            "present_elements": present,
        },
        details={
            "interpretation": (
                "A low semantic-tag count alone is not treated as a significant "
                "defect. Page purpose and content structure require context."
            ),
            "impact": "informational",
            "scope": "page",
        },
    )


def run_checks(html: str) -> List[Observation]:
    """
    Run all structured-data and machine-readable-content checks.

    SD-001 through SD-007 correspond to the supplied structured-data reference.
    SD-008 through SD-013 implement the additional checks described in SKILL.md.
    """
    return [
        check_structured_data_presence(html),
        check_json_ld_validity(html),
        check_schema_types(html),
        check_schema_properties(html),
        check_schema_consistency(html),
        check_duplicate_or_conflicting_schema(html),
        check_breadcrumb_structure(html),
        check_heading_structure(html),
        check_meta_description(html),
        check_open_graph_metadata(html),
        check_twitter_metadata(html),
        check_image_alt_text(html),
        check_semantic_html(html),
    ]