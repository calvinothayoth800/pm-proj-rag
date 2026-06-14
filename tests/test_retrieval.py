import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.retrieval.index import build_index, load_index
from pm_rag.core.retrieval.search import search


def test_build_and_search_index():
    # Build index from existing processed chunks
    out = build_index()
    idx = load_index(str(out))
    assert "entries" in idx and idx["entries"], "index has no entries"
    # Simple query — should return entries with metadata source_url from corpus
    results = search("exit load")
    assert results, "search returned no results"
    for r in results:
        assert r.get("metadata") and r["metadata"].get("source_url"), "result missing source_url"
