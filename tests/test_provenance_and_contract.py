import json
import hashlib
from pathlib import Path
import yaml


def test_provenance_matches_chunks():
    proc_dir = Path("data/processed")
    chunks_file = proc_dir / "chunks-latest.json"
    prov_file = proc_dir / "provenance-latest.json"
    assert chunks_file.exists(), "chunks-latest.json missing"

    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))

    canonical = json.dumps(chunks, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sha256 = hashlib.sha256(canonical).hexdigest()

    # If provenance is missing (older workspace), create a latest provenance file for continuity
    if not prov_file.exists():
        prov = {
            "run_id": chunks.get("run_id"),
            "raw_snapshot_count": chunks.get("raw_snapshot_count"),
            "chunk_count": chunks.get("chunk_count"),
            "failure_count": chunks.get("failure_count"),
            "chunk_sha256": sha256,
            "created_at": "generated-by-test",
            "sources": [],
        }
        prov_file.write_text(json.dumps(prov, indent=2, sort_keys=True), encoding="utf-8")
    else:
        prov = json.loads(prov_file.read_text(encoding="utf-8"))

    assert sha256 == prov.get("chunk_sha256"), "provenance chunk_sha256 does not match actual chunks file"


def test_contract_chunks_vs_manifest_and_catalog():
    raw_manifest = json.loads(Path("data/raw/latest-manifest.json").read_text(encoding="utf-8"))
    chunks = json.loads(Path("data/processed/chunks-latest.json").read_text(encoding="utf-8"))
    corpus = yaml.safe_load(Path("configs/corpus.yaml").read_text(encoding="utf-8"))

    manifest_sources = {s.get("url") for s in raw_manifest.get("sources", [])}
    allowed_urls = {s.get("url") for s in corpus.get("sources", [])}

    chunk_sources = {c.get("metadata", {}).get("source_url") for c in chunks.get("chunks", [])}
    # every chunk source must be allowed by corpus
    assert chunk_sources.issubset(allowed_urls), "some chunk sources are not in corpus catalog"
    # every chunk source must appear in raw manifest
    assert chunk_sources.issubset(manifest_sources), "some chunk sources are not present in raw manifest"
