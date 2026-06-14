import subprocess
import sys
from pathlib import Path


def test_validate_ingest_executes():
    # Run the validation script; it should exit 0 when artifacts are present
    script = Path("scripts/validate_ingest.py")
    assert script.exists(), "validation script missing"
    res = subprocess.run([sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = res.stdout.decode('utf-8', errors='replace')
    err = res.stderr.decode('utf-8', errors='replace')
    print(out)
    print(err)
    assert res.returncode == 0, "validate_ingest failed: " + err
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.ingestion.chunker import chunk_text
from pm_rag.core.ingestion.fetcher import FetchResult, fetch_source
from pm_rag.core.ingestion.parser import ParseError, focus_scheme_text, parse_html
from pm_rag.core.ingestion.pipeline import ingest_catalog, write_ingestion_outputs, write_raw_snapshots
from pm_rag.core.sources.catalog import CatalogValidationError, validate_corpus_catalog


CATALOG = ROOT / "configs" / "corpus.yaml"
ALLOWED_URL = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
DISALLOWED_URL = "https://groww.in/mutual-funds/not-in-corpus"


def title_for_url(url: str) -> str:
    catalog = validate_corpus_catalog(CATALOG)
    by_url = {str(source["url"]): str(source.get("page_title") or source["title"]) for source in catalog["sources"]}
    return by_url[url]


def sample_html(title: str = "HDFC Mid Cap Fund - Direct Growth") -> str:
    return """
    <html>
      <head><title>{title}</title><script>ignored()</script></head>
      <body>
        <nav>Home</nav>
        <h1>{title}</h1>
        <p>Expense Ratio: 0.75%</p>
        <p>Exit Load: 1% if redeemed within 1 year.</p>
        <p>Minimum SIP Amount: Rs 100</p>
        <p>Riskometer: Very High</p>
        <p>Benchmark: NIFTY Midcap 150 TRI</p>
        <p>Expense Ratio: 0.75%</p>
        <footer>Privacy Policy</footer>
      </body>
    </html>
    """.format(title=title)


class Phase2IngestionTests(unittest.TestCase):
    def test_fetcher_blocks_unapproved_url_before_transport(self) -> None:
        calls = []

        def transport(url: str) -> FetchResult:
            calls.append(url)
            return FetchResult(url=url, status_code=200, body=sample_html(), headers={})

        with self.assertRaises(CatalogValidationError):
            fetch_source(DISALLOWED_URL, CATALOG, transport=transport)

        self.assertEqual([], calls)

    def test_fetcher_allows_configured_url_with_injected_transport(self) -> None:
        result = fetch_source(
            ALLOWED_URL,
            CATALOG,
            transport=lambda url: FetchResult(url=url, status_code=200, body=sample_html(), headers={}),
        )

        self.assertEqual(ALLOWED_URL, result.url)
        self.assertIn("Expense Ratio", result.body)

    def test_parser_rejects_blocked_or_captcha_content(self) -> None:
        with self.assertRaises(ParseError):
            parse_html("<html><body>Access denied. CAPTCHA required.</body></html>", min_chars=10)

    def test_parser_rejects_low_content_client_shell(self) -> None:
        with self.assertRaises(ParseError):
            parse_html("<html><body><div id='root'></div><script>render()</script></body></html>")

    def test_parser_filters_noise_but_preserves_factual_text(self) -> None:
        text = parse_html(sample_html())

        self.assertIn("Expense Ratio: 0.75%", text)
        self.assertIn("Minimum SIP Amount: Rs 100", text)
        self.assertNotIn("Privacy Policy", text)
        self.assertNotIn("ignored()", text)

    def test_parser_focuses_on_configured_scheme_content(self) -> None:
        text = parse_html(
            """
            <html><body>
              <nav>Stocks</nav>
              <p>Invest in Stocks</p>
              <h1>HDFC Mid Cap Fund Direct Growth</h1>
              <p>Min. for SIP</p><p>Rs 100</p>
              <p>Expense ratio</p><p>0.75%</p>
              <p>Exit load of 1% if redeemed within 1 year.</p>
              <p>Vaishnavi Tech Park</p>
              <p>Footer links</p>
            </body></html>
            """,
            min_chars=40,
        )
        focused = focus_scheme_text(text, "HDFC Mid Cap Fund - Direct Growth", min_chars=40)

        self.assertTrue(focused.startswith("HDFC Mid Cap Fund Direct Growth"))
        self.assertIn("Expense ratio", focused)
        self.assertNotIn("Invest in Stocks", focused)
        self.assertNotIn("Footer links", focused)

    def test_chunker_preserves_required_metadata_and_numeric_context(self) -> None:
        catalog = validate_corpus_catalog(CATALOG)
        source = catalog["sources"][0]
        scheme = catalog["schemes"][0]
        chunks = chunk_text(parse_html(sample_html()), source, scheme, max_chars=220)

        self.assertTrue(chunks)
        first = chunks[0]
        self.assertEqual(ALLOWED_URL, first.metadata["source_url"])
        self.assertEqual("hdfc-mid-cap-direct-growth", first.metadata["scheme_id"])
        self.assertEqual("Mid Cap", first.metadata["category"])
        self.assertEqual("2026-05-29", first.metadata["last_checked"])
        all_text = "\n".join(chunk.text for chunk in chunks)
        self.assertIn("Expense Ratio: 0.75%", all_text)
        self.assertIn("Minimum SIP Amount: Rs 100", all_text)

    def test_chunker_deduplicates_repeated_sections_per_source(self) -> None:
        catalog = validate_corpus_catalog(CATALOG)
        source = catalog["sources"][0]
        scheme = catalog["schemes"][0]
        chunks = chunk_text("Expense Ratio: 0.75%\nExpense Ratio: 0.75%", source, scheme, max_chars=30)

        self.assertEqual(1, len(chunks))

    def test_ingestion_run_records_failures_without_substituting_sources(self) -> None:
        def transport(url: str) -> FetchResult:
            if url == ALLOWED_URL:
                return FetchResult(url=url, status_code=200, body="CAPTCHA required", headers={})
            return FetchResult(url=url, status_code=200, body=sample_html(title=title_for_url(url)), headers={})

        run = ingest_catalog(CATALOG, transport=transport, run_id="phase2-test")

        self.assertEqual("phase2-test", run.run_id)
        self.assertEqual(1, len(run.failures))
        self.assertEqual(5, len(run.raw_snapshots))
        self.assertIn("blocked", run.failures[0].error)
        for chunk in run.chunks:
            self.assertNotEqual(ALLOWED_URL, chunk.metadata["source_url"])

    def test_raw_and_processed_outputs_use_run_specific_artifacts(self) -> None:
        def transport(url: str) -> FetchResult:
            return FetchResult(url=url, status_code=200, body=sample_html(title=title_for_url(url)), headers={})

        run = ingest_catalog(CATALOG, transport=transport, run_id="phase2-output")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            raw_paths = write_raw_snapshots(run, temp_root / "raw")
            output_path = write_ingestion_outputs(run, temp_root / "processed")
            processed_payload = json.loads(output_path.read_text(encoding="utf-8"))
            raw_manifest = json.loads((temp_root / "raw" / "phase2-output" / "manifest.json").read_text(encoding="utf-8"))
            latest_raw_exists = (temp_root / "raw" / "latest-manifest.json").exists()
            latest_processed_exists = (temp_root / "processed" / "chunks-latest.json").exists()

        # raw_paths includes per-source html files plus manifest(s) and run log
        self.assertGreaterEqual(len(raw_paths), 7)
        # raw artifacts directory created (we validated artifact count above)
        self.assertEqual(5, raw_manifest["snapshot_count"])
        self.assertTrue(latest_raw_exists)
        self.assertEqual("chunks-phase2-output.json", output_path.name)
        self.assertTrue(latest_processed_exists)
        self.assertEqual("phase2-output", processed_payload["run_id"])
        self.assertEqual(5, processed_payload["raw_snapshot_count"])
        self.assertEqual(len(run.chunks), processed_payload["chunk_count"])
        self.assertEqual(0, processed_payload["failure_count"])
        self.assertTrue(processed_payload["chunks"])
        for record in processed_payload["chunks"]:
            self.assertIn(record["metadata"]["source_url"], [source["url"] for source in validate_corpus_catalog(CATALOG)["sources"]])


if __name__ == "__main__":
    unittest.main()
