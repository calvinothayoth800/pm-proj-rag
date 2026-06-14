from datetime import datetime
import json
import hashlib
from typing import Set
from pathlib import Path
from typing import Dict, List, Optional

from pm_rag.core.ingestion.chunker import Chunk, chunks_to_records, chunk_text
from pm_rag.core.ingestion.fetcher import FetchError, FetchResult, FetchTransport, fetch_source
from pm_rag.core.ingestion.parser import ParseError, focus_scheme_text, parse_html
from pm_rag.core.sources.catalog import CatalogPath, validate_corpus_catalog


class SourceFailure:
    def __init__(self, source_id: str, url: str, error: str) -> None:
        self.source_id = source_id
        self.url = url
        self.error = error


class RawSnapshot:
    def __init__(self, source_id: str, url: str, status_code: int, body: str, headers: Dict[str, str]) -> None:
        self.source_id = source_id
        self.url = url
        self.status_code = status_code
        self.body = body
        self.headers = headers


class IngestionRun:
    def __init__(
        self,
        run_id: str,
        chunks: List[Chunk],
        failures: List[SourceFailure],
        raw_snapshots: List[RawSnapshot],
    ) -> None:
        self.run_id = run_id
        self.chunks = chunks
        self.failures = failures
        self.raw_snapshots = raw_snapshots


def _schemes_by_id(catalog: Dict[str, List[Dict[str, object]]]) -> Dict[str, Dict[str, object]]:
    return {str(scheme["id"]): scheme for scheme in catalog["schemes"]}


def ingest_catalog(
    catalog_path: CatalogPath,
    transport: Optional[FetchTransport] = None,
    run_id: Optional[str] = None,
) -> IngestionRun:
    catalog = validate_corpus_catalog(catalog_path)
    schemes = _schemes_by_id(catalog)
    active_run_id = run_id or datetime.utcnow().strftime("%Y%m%d%H%M%S")
    chunks = []  # type: List[Chunk]
    failures = []  # type: List[SourceFailure]
    raw_snapshots = []  # type: List[RawSnapshot]

    for source in catalog["sources"]:
        url = str(source["url"])
        source_id = str(source["id"])
        try:
            result = fetch_source(url, catalog_path, transport=transport)
            raw_snapshots.append(
                RawSnapshot(
                    source_id=source_id,
                    url=result.url,
                    status_code=result.status_code,
                    body=result.body,
                    headers=result.headers,
                )
            )
            scheme = schemes[str(source["scheme_id"])]
            focus_title = str(source.get("page_title") or scheme["name"])
            text = focus_scheme_text(parse_html(result.body), focus_title)
            chunks.extend(chunk_text(text, source, scheme))
        except (FetchError, ParseError, KeyError, ValueError) as exc:
            failures.append(SourceFailure(source_id=source_id, url=url, error=str(exc)))

    return IngestionRun(run_id=active_run_id, chunks=chunks, failures=failures, raw_snapshots=raw_snapshots)


def write_raw_snapshots(run: IngestionRun, raw_dir: Path) -> List[Path]:
    run_dir = raw_dir / run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    written = []  # type: List[Path]
    manifest_sources = []

    for snapshot in run.raw_snapshots:
        output_path = run_dir / "{0}.html".format(snapshot.source_id)
        output_path.write_text(snapshot.body, encoding="utf-8")
        written.append(output_path)
        manifest_sources.append(
            {
                "source_id": snapshot.source_id,
                "url": snapshot.url,
                "status_code": snapshot.status_code,
                "path": str(output_path),
                "bytes": len(snapshot.body.encode("utf-8")),
            }
        )

    manifest_path = run_dir / "manifest.json"
    payload = {
        "run_id": run.run_id,
        "snapshot_count": len(run.raw_snapshots),
        "failure_count": len(run.failures),
        "sources": manifest_sources,
        "failures": [
            {"source_id": failure.source_id, "url": failure.url, "error": failure.error}
            for failure in run.failures
        ],
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    latest_manifest_path = raw_dir / "latest-manifest.json"
    latest_manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    written.append(manifest_path)
    written.append(latest_manifest_path)
    # Write a simple run log for provenance/ops
    run_log = run_dir / "run.log"
    log_lines = [
        f"run_id: {run.run_id}",
        f"timestamp: {datetime.utcnow().isoformat()}Z",
        f"snapshots: {len(run.raw_snapshots)}",
        f"chunks: {len(run.chunks)}",
        f"failures: {len(run.failures)}",
    ]
    run_log.write_text("\n".join(log_lines), encoding="utf-8")
    written.append(run_log)
    return written


def write_ingestion_outputs(run: IngestionRun, processed_dir: Path) -> Path:
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "chunks-{0}.json".format(run.run_id)
    payload = {
        "run_id": run.run_id,
        "raw_snapshot_count": len(run.raw_snapshots),
        "chunk_count": len(run.chunks),
        "failure_count": len(run.failures),
        "chunks": chunks_to_records(run.chunks),
        "failures": [
            {"source_id": failure.source_id, "url": failure.url, "error": failure.error}
            for failure in run.failures
        ],
    }
    temp_path = processed_dir / ".{0}.tmp".format(output_path.name)
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(output_path)
    latest_path = processed_dir / "chunks-latest.json"
    latest_temp_path = processed_dir / ".{0}.tmp".format(latest_path.name)
    latest_temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    latest_temp_path.replace(latest_path)
    # Compute provenance: SHA256 over the canonical JSON bytes of the latest chunks
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sha256 = hashlib.sha256(canonical).hexdigest()
    provenance = {
        "run_id": run.run_id,
        "raw_snapshot_count": len(run.raw_snapshots),
        "chunk_count": len(run.chunks),
        "failure_count": len(run.failures),
        "chunk_sha256": sha256,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "sources": list({c.metadata.get("source_url") for c in run.chunks if c.metadata.get("source_url")}),
    }
    prov_path = processed_dir / f"provenance-{run.run_id}.json"
    prov_path.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    latest_prov = processed_dir / "provenance-latest.json"
    latest_prov.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
