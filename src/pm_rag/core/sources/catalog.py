from pathlib import Path
from typing import Dict, List, Optional, Union


EXPECTED_SCHEME_COUNT = 5
EXPECTED_SOURCE_COUNT = 5
GROWW_MUTUAL_FUND_PREFIX = "https://groww.in/mutual-funds/"
REQUIRED_SCHEME_FIELDS = ("id", "name", "category")
REQUIRED_SOURCE_FIELDS = ("id", "title", "url", "type", "scheme_id", "allowed", "last_checked")


class CatalogValidationError(ValueError):
    """Raised when the fixed source catalog violates project rules."""


CatalogPath = Union[str, Path]
CatalogItem = Dict[str, object]


def _parse_scalar(value: str) -> object:
    cleaned = value.strip().strip('"').strip("'")
    if cleaned.lower() == "true":
        return True
    if cleaned.lower() == "false":
        return False
    return cleaned


def _parse_list_section(text: str, section_name: str) -> List[CatalogItem]:
    items = []  # type: List[CatalogItem]
    current = None  # type: Optional[CatalogItem]
    in_section = False

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if not raw_line.startswith(" ") and raw_line.rstrip() == section_name + ":":
            in_section = True
            current = None
            continue

        if in_section and not raw_line.startswith(" "):
            break

        if not in_section:
            continue

        stripped = raw_line.strip()
        if stripped.startswith("- "):
            if current is not None:
                items.append(current)
            current = {}
            stripped = stripped[2:]

        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = _parse_scalar(value)

    if current is not None:
        items.append(current)

    return items


def load_catalog(catalog_path: CatalogPath) -> Dict[str, List[CatalogItem]]:
    text = Path(catalog_path).read_text(encoding="utf-8")
    return {
        "schemes": _parse_list_section(text, "schemes"),
        "sources": _parse_list_section(text, "sources"),
    }


def load_allowed_urls(catalog_path: CatalogPath) -> List[str]:
    catalog = load_catalog(catalog_path)
    return [str(source.get("url", "")) for source in catalog["sources"] if source.get("url")]


def _missing_fields(item: CatalogItem, fields: tuple) -> List[str]:
    return [field for field in fields if field not in item or item[field] in ("", None)]


def validate_fixed_corpus(catalog_path: CatalogPath) -> List[str]:
    catalog = load_catalog(catalog_path)
    schemes = catalog["schemes"]
    sources = catalog["sources"]
    urls = [str(source.get("url", "")) for source in sources if source.get("url")]
    errors = []  # type: List[str]

    if len(schemes) != EXPECTED_SCHEME_COUNT:
        errors.append(f"expected {EXPECTED_SCHEME_COUNT} schemes, found {len(schemes)}")

    if len(urls) != EXPECTED_SOURCE_COUNT:
        errors.append(f"expected {EXPECTED_SOURCE_COUNT} source URLs, found {len(urls)}")

    if len(sources) != EXPECTED_SOURCE_COUNT:
        errors.append(f"expected {EXPECTED_SOURCE_COUNT} source records, found {len(sources)}")

    scheme_ids = [str(scheme.get("id", "")) for scheme in schemes if scheme.get("id")]
    duplicate_scheme_ids = sorted({scheme_id for scheme_id in scheme_ids if scheme_ids.count(scheme_id) > 1})
    if duplicate_scheme_ids:
        errors.append(f"duplicate scheme IDs: {', '.join(duplicate_scheme_ids)}")

    for index, scheme in enumerate(schemes, start=1):
        missing = _missing_fields(scheme, REQUIRED_SCHEME_FIELDS)
        if missing:
            errors.append(f"scheme {index} missing fields: {', '.join(missing)}")

    source_ids = [str(source.get("id", "")) for source in sources if source.get("id")]
    duplicate_source_ids = sorted({source_id for source_id in source_ids if source_ids.count(source_id) > 1})
    if duplicate_source_ids:
        errors.append(f"duplicate source IDs: {', '.join(duplicate_source_ids)}")

    for index, source in enumerate(sources, start=1):
        missing = _missing_fields(source, REQUIRED_SOURCE_FIELDS)
        if missing:
            errors.append(f"source {index} missing fields: {', '.join(missing)}")

        if source.get("allowed") is not True:
            errors.append(f"source {index} must set allowed: true")

        if source.get("type") != "groww_scheme_page":
            errors.append(f"source {index} must use type: groww_scheme_page")

        scheme_id = str(source.get("scheme_id", ""))
        if scheme_id and scheme_id not in scheme_ids:
            errors.append(f"source {index} references unknown scheme_id: {scheme_id}")

    duplicate_urls = sorted({url for url in urls if urls.count(url) > 1})
    if duplicate_urls:
        errors.append(f"duplicate source URLs: {', '.join(duplicate_urls)}")

    outside_groww = [url for url in urls if not url.startswith(GROWW_MUTUAL_FUND_PREFIX)]
    if outside_groww:
        errors.append(f"non-Groww mutual fund URLs: {', '.join(outside_groww)}")

    if errors:
        raise CatalogValidationError("; ".join(errors))

    return urls


def validate_corpus_catalog(catalog_path: CatalogPath) -> Dict[str, List[CatalogItem]]:
    validate_fixed_corpus(catalog_path)
    return load_catalog(catalog_path)


def is_allowed_url(url: str, catalog_path: CatalogPath) -> bool:
    return url in validate_fixed_corpus(catalog_path)


def assert_allowed_url(url: str, catalog_path: CatalogPath) -> None:
    if not is_allowed_url(url, catalog_path):
        raise CatalogValidationError(f"URL is outside the fixed Groww corpus: {url}")
