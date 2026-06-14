from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.sources.catalog import (
    CatalogValidationError,
    assert_allowed_url,
    validate_fixed_corpus,
)


DOCS = ROOT / "docs"
CATALOG = ROOT / "configs" / "corpus.yaml"

EXPECTED_URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Phase0FoundationTests(unittest.TestCase):
    def test_architecture_contains_fixed_corpus_table(self) -> None:
        architecture = read(DOCS / "architecture.md")

        self.assertIn("## Fixed Project Corpus", architecture)
        self.assertIn("These five Groww URLs are the entire corpus", architecture)
        for url in EXPECTED_URLS:
            self.assertIn(url, architecture)

    def test_catalog_contains_exactly_five_allowed_groww_sources(self) -> None:
        urls = validate_fixed_corpus(CATALOG)

        self.assertEqual(EXPECTED_URLS, urls)

    def test_catalog_validator_rejects_urls_outside_fixed_corpus(self) -> None:
        allowed = EXPECTED_URLS[0]
        disallowed = "https://groww.in/mutual-funds/some-other-fund"

        assert_allowed_url(allowed, CATALOG)
        with self.assertRaises(CatalogValidationError):
            assert_allowed_url(disallowed, CATALOG)

    def test_handoff_records_active_source_boundary(self) -> None:
        handoff = read(DOCS / "handoff.md")

        self.assertIn("five fixed Groww scheme pages", handoff)
        self.assertIn("No other URLs are allowed", handoff)
        self.assertIn("docs/edge-cases/", handoff)
        for url in EXPECTED_URLS:
            self.assertIn(url, handoff)

    def test_readme_matches_phase0_source_and_disclaimer_rules(self) -> None:
        readme = read(ROOT / "README.md")

        self.assertIn("Facts-only. No investment advice.", readme)
        self.assertIn("Only the five exact Groww URLs", readme)
        self.assertNotIn("15-25 official", readme)
        for url in EXPECTED_URLS:
            self.assertIn(url, readme)

    def test_canonical_project_docs_live_under_docs_folder(self) -> None:
        self.assertTrue((DOCS / "architecture.md").exists())
        self.assertTrue((DOCS / "handoff.md").exists())
        self.assertTrue((DOCS / "problemstatement.md").exists())

    def test_phase0_edge_case_checks_are_represented_in_tests(self) -> None:
        edge_cases = read(DOCS / "edge-cases" / "phase-0-foundation.md")

        checks = re.findall(r"^- `([^`]+)`", edge_cases, flags=re.MULTILINE)
        self.assertIn("docs/architecture.md", checks)
        self.assertIn("configs/corpus.yaml", checks)
        self.assertIn("docs/handoff.md", checks)


if __name__ == "__main__":
    unittest.main()
