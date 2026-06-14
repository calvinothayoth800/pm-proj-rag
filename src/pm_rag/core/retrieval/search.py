import math
from typing import List, Dict

from pm_rag.core.retrieval.index import load_index
from pm_rag.core.retrieval.embedder import embed_text


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def search(query: str, top_k: int = 3, index_path: str = "data/indexes/index.json") -> List[Dict]:
    idx = load_index(index_path)
    qemb = embed_text(query, dim=idx.get("dim", 128))
    results = []
    for entry in idx.get("entries", []):
        score = _dot(qemb, entry["embedding"])  # embeddings normalized, dot=cosine
        results.append({"id": entry["id"], "score": score, "metadata": entry.get("metadata"), "text": entry.get("text")})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]
