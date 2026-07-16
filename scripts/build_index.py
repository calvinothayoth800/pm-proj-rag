from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.retrieval.faiss_index import build_faiss_index
from pm_rag.core.retrieval.index import build_index


def main() -> int:
    print("Building FAISS vector index...")
    out_faiss = build_faiss_index()
    print(f"[OK] FAISS Index built successfully at: {out_faiss}")
    
    print("Building classic JSON index...")
    out_classic = build_index()
    print(f"[OK] Classic Index built successfully at: {out_classic}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
