import json
from pathlib import Path
from typing import Dict, List

from pm_rag.core.retrieval.embedder import embed_text


def build_index(processed_path: str = "data/processed/chunks-latest.json", index_dir: str = "data/indexes", dim: int = 384) -> Path:
    proc = Path(processed_path)
    assert proc.exists(), f"processed chunks not found at {processed_path}"
    payload = json.loads(proc.read_text(encoding="utf-8"))
    entries = []  # type: List[Dict]
    for rec in payload.get("chunks", []):
        text = rec.get("text", "")
        emb = embed_text(text, dim=dim)
        entries.append({
            "id": rec.get("id"),
            "embedding": emb,
            "metadata": rec.get("metadata", {}),
            "text": text,
        })

    idx_dir = Path(index_dir)
    idx_dir.mkdir(parents=True, exist_ok=True)
    out = idx_dir / "index.json"
    out.write_text(json.dumps({"dim": dim, "entries": entries}, indent=2), encoding="utf-8")
    return out


def load_index(index_path: str = "data/indexes/index.json") -> Dict:
    p = Path(index_path)
    if not p.exists():
        raise FileNotFoundError(index_path)
    return json.loads(p.read_text(encoding="utf-8"))
