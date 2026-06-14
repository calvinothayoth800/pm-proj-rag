from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.ingestion.pipeline import ingest_catalog, write_ingestion_outputs, write_raw_snapshots
import subprocess
import sys

CATALOG = ROOT / "configs" / "corpus.yaml"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def main() -> int:
    run = ingest_catalog(CATALOG)
    raw_paths = write_raw_snapshots(run, RAW)
    output_path = write_ingestion_outputs(run, PROCESSED)
    print(
        "Wrote {0} raw artifacts, {1} chunks, and {2} failures to {3}".format(
            len(raw_paths),
            len(run.chunks),
            len(run.failures),
            output_path,
        )
    )
    # Run post-ingest validation to ensure artifacts are consistent.
    validator = [sys.executable, str(Path(__file__).resolve().parents[1] / "scripts" / "validate_ingest.py")]
    res = subprocess.run(validator)
    if res.returncode != 0:
        print("Post-ingest validation failed; see validate_ingest output.")
        return 2
    return 1 if run.failures else 0


if __name__ == "__main__":
    sys.exit(main())
