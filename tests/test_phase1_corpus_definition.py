from pathlib import Path
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.sources.catalog import (
    CatalogValidationError,
    assert_allowed_url,
    load_catalog,
    validate_corpus_catalog,
)


CATALOG = ROOT / "configs" / "corpus.yaml"

EXPECTED_URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
]


def write_temp_catalog(text: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml", encoding="utf-8")
    with handle:
        handle.write(textwrap.dedent(text).strip() + "\n")
    return Path(handle.name)


def write_raw_temp_catalog(text: str) -> Path:
    handle = tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml", encoding="utf-8")
    with handle:
        handle.write(text)
    return Path(handle.name)


class Phase1CorpusDefinitionTests(unittest.TestCase):
    def test_catalog_registers_exactly_five_schemes_and_sources(self) -> None:
        catalog = validate_corpus_catalog(CATALOG)

        self.assertEqual(5, len(catalog["schemes"]))
        self.assertEqual(5, len(catalog["sources"]))

    def test_every_source_has_required_phase1_metadata(self) -> None:
        catalog = validate_corpus_catalog(CATALOG)

        for source in catalog["sources"]:
            self.assertIs(source["allowed"], True)
            self.assertEqual("groww_scheme_page", source["type"])
            self.assertIn("scheme_id", source)
            self.assertIn("last_checked", source)
            self.assertIn("page_title", source)

    def test_every_source_references_a_configured_scheme(self) -> None:
        catalog = validate_corpus_catalog(CATALOG)
        scheme_ids = {scheme["id"] for scheme in catalog["schemes"]}

        for source in catalog["sources"]:
            self.assertIn(source["scheme_id"], scheme_ids)

    def test_source_urls_are_exact_allowlist_matches(self) -> None:
        for url in EXPECTED_URLS:
            assert_allowed_url(url, CATALOG)

        variants = [
            EXPECTED_URLS[0] + "/",
            EXPECTED_URLS[0] + "?utm_source=test",
            EXPECTED_URLS[0].upper(),
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth#overview",
        ]

        for variant in variants:
            with self.subTest(variant=variant):
                with self.assertRaises(CatalogValidationError):
                    assert_allowed_url(variant, CATALOG)

    def test_catalog_rejects_extra_linked_or_discovered_sources(self) -> None:
        base = CATALOG.read_text(encoding="utf-8")
        extra = (
            "  - id: linked-factsheet\n"
            "    title: Linked Factsheet\n"
            "    url: https://www.hdfcfund.com/factsheet.pdf\n"
            "    type: factsheet\n"
            "    scheme_id: hdfc-mid-cap-direct-growth\n"
            "    allowed: true\n"
            "    last_checked: 2026-05-29\n"
        )
        temp_catalog = write_raw_temp_catalog(base + "\n" + extra)

        with self.assertRaises(CatalogValidationError) as error:
            validate_corpus_catalog(temp_catalog)

        message = str(error.exception)
        self.assertIn("expected 5 source URLs", message)
        self.assertIn("non-Groww mutual fund URLs", message)

    def test_catalog_rejects_missing_required_source_fields(self) -> None:
        temp_catalog = write_temp_catalog(
            """
            schemes:
              - id: hdfc-mid-cap-direct-growth
                name: HDFC Mid Cap Fund - Direct Growth
                category: Mid Cap
              - id: hdfc-equity-direct-growth
                name: HDFC Equity Fund - Direct Growth
                category: Flexi Cap
              - id: hdfc-focused-direct-growth
                name: HDFC Focused Fund - Direct Growth
                category: Focused
              - id: hdfc-elss-tax-saver-direct-plan-growth
                name: HDFC ELSS Tax Saver - Direct Plan Growth
                category: ELSS
              - id: hdfc-large-cap-direct-growth
                name: HDFC Large Cap Fund - Direct Growth
                category: Large Cap
            sources:
              - id: hdfc-mid-cap-direct-growth-groww
                title: HDFC Mid Cap Fund - Direct Growth
                url: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
                scheme_id: hdfc-mid-cap-direct-growth
                allowed: true
            """
        )

        with self.assertRaises(CatalogValidationError) as error:
            validate_corpus_catalog(temp_catalog)

        message = str(error.exception)
        self.assertIn("missing fields", message)
        self.assertIn("type", message)
        self.assertIn("last_checked", message)

    def test_catalog_rejects_unknown_scheme_references(self) -> None:
        text = CATALOG.read_text(encoding="utf-8").replace(
            "scheme_id: hdfc-mid-cap-direct-growth",
            "scheme_id: not-a-configured-scheme",
            1,
        )
        temp_catalog = write_temp_catalog(text)

        with self.assertRaises(CatalogValidationError) as error:
            validate_corpus_catalog(temp_catalog)

        self.assertIn("unknown scheme_id", str(error.exception))

    def test_catalog_loader_preserves_scheme_names_for_manual_rename_review(self) -> None:
        catalog = load_catalog(CATALOG)
        names_by_id = {scheme["id"]: scheme["name"] for scheme in catalog["schemes"]}

        self.assertEqual(
            "HDFC ELSS Tax Saver - Direct Plan Growth",
            names_by_id["hdfc-elss-tax-saver-direct-plan-growth"],
        )


if __name__ == "__main__":
    unittest.main()
