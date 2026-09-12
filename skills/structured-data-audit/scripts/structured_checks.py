import json

from bs4 import BeautifulSoup

from shared.models import Observation


def extract_json_ld(html: str):

    soup = BeautifulSoup(html, "html.parser")

    blocks = []

    for tag in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"}
    ):
        raw = tag.string or tag.get_text()

        blocks.append(raw.strip())

    return blocks


def check_structured_data_presence(html: str) -> Observation:

    blocks = extract_json_ld(html)

    return Observation(
        check="SD-001",
        found=len(blocks) > 0,
        evidence={
            "json_ld_blocks": len(blocks)
        }
    )


def check_json_ld_validity(html: str) -> Observation:

    blocks = extract_json_ld(html)

    valid = []
    invalid = []

    for index, block in enumerate(blocks):

        try:
            data = json.loads(block)

            valid.append({
                "index": index,
                "type": type(data).__name__
            })

        except json.JSONDecodeError as e:

            invalid.append({
                "index": index,
                "error": str(e)
            })

    return Observation(
        check="SD-002",
        found=len(invalid) > 0,
        evidence={
            "total": len(blocks),
            "valid": valid,
            "invalid": invalid
        }
    )


def extract_schema_types(data):

    types = []

    if isinstance(data, dict):

        if "@type" in data:
            value = data["@type"]

            if isinstance(value, list):
                types.extend(value)
            else:
                types.append(value)

        for value in data.values():
            types.extend(extract_schema_types(value))

    elif isinstance(data, list):

        for item in data:
            types.extend(extract_schema_types(item))

    return types


def check_schema_types(html: str) -> Observation:

    blocks = extract_json_ld(html)

    types = []

    for block in blocks:

        try:
            data = json.loads(block)
            types.extend(extract_schema_types(data))

        except json.JSONDecodeError:
            continue

    return Observation(
        check="SD-003",
        found=len(types) > 0,
        evidence={
            "types": sorted(set(types))
        }
    )


def check_schema_properties(html: str) -> Observation:

    blocks = extract_json_ld(html)

    results = []

    for block_index, block in enumerate(blocks):

        try:
            data = json.loads(block)

        except json.JSONDecodeError:
            continue

        if not isinstance(data, dict):
            continue

        schema_type = data.get("@type")

        if isinstance(schema_type, list):
            schema_type = schema_type[0] if schema_type else None

        if schema_type == "Product":

            properties = [
                "name",
                "description",
                "image",
                "offers"
            ]

            results.append({
                "type": "Product",
                "present": {
                    prop: prop in data
                    for prop in properties
                }
            })

        elif schema_type == "Article":

            properties = [
                "headline",
                "author",
                "datePublished",
                "dateModified"
            ]

            results.append({
                "type": "Article",
                "present": {
                    prop: prop in data
                    for prop in properties
                }
            })

        elif schema_type == "Organization":

            properties = [
                "name",
                "url",
                "logo"
            ]

            results.append({
                "type": "Organization",
                "present": {
                    prop: prop in data
                    for prop in properties
                }
            })

    return Observation(
        check="SD-004",
        found=len(results) > 0,
        evidence=results
    )


def run_checks(html: str):

    return [
        check_structured_data_presence(html),
        check_json_ld_validity(html),
        check_schema_types(html),
        check_schema_properties(html),
    ]