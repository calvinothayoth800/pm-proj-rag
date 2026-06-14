import json
import sys
from pathlib import Path

import yaml


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(manifest_path: str = "data/raw/latest-manifest.json",
             chunks_path: str = "data/processed/chunks-latest.json",
             corpus_path: str = "configs/corpus.yaml") -> bool:
    manifest = load_json(Path(manifest_path))
    chunks = load_json(Path(chunks_path))
    corpus = load_yaml(Path(corpus_path))

    # Basic counts
    snapshot_count = manifest.get("snapshot_count", 0)
    manifest_sources = [s.get("url") for s in manifest.get("sources", [])]

    if snapshot_count != len(manifest.get("sources", [])):
        raise AssertionError("snapshot_count mismatch with manifest sources")

    chunk_count = chunks.get("chunk_count", 0)
    actual_chunks = len(chunks.get("chunks", []))
    if chunk_count != actual_chunks:
        raise AssertionError("chunk_count does not match number of chunk objects")

    if chunk_count == 0:
        raise AssertionError("no chunks found in processed data")

    # Allowed urls from corpus
    allowed_urls = {s.get("url") for s in corpus.get("sources", [])}

    # Check that every chunk's source_url is allowed and seen in manifest
    seen_sources = set()
    for c in chunks.get("chunks", []):
        meta = c.get("metadata", {})
        src = meta.get("source_url")
        if not src:
            raise AssertionError(f"chunk {c.get('id')} missing source_url")
        if src not in allowed_urls:
            raise AssertionError(f"chunk {c.get('id')} has disallowed source_url: {src}")
        seen_sources.add(src)

    # Ensure all seen_sources are present in manifest
    for src in seen_sources:
        if src not in manifest_sources:
            raise AssertionError(f"source {src} present in chunks but missing from manifest")

    return True


def main():
    try:
        ok = validate()
    except Exception as e:
        print("Validation failed:", e)
        sys.exit(2)
    print("Ingest validation passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
