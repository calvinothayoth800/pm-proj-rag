from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.retrieval.faiss_index import build_faiss_index


def main() -> int:
    print("Building FAISS vector index...")
    out = build_faiss_index()
    print(f"[OK] Index built successfully at: {out}")
    print(f"[OK] Use this index for fast vector similarity search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
