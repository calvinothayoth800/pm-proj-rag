import hashlib
import re
from typing import Dict, Iterable, List


class Chunk:
    def __init__(self, id: str, text: str, metadata: Dict[str, object]) -> None:
        self.id = id
        self.text = text
        self.metadata = metadata


def _normalize_for_hash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _source_metadata(source: Dict[str, object], scheme: Dict[str, object]) -> Dict[str, object]:
    return {
        "source_url": source["url"],
        "source_title": source["title"],
        "source_type": source["type"],
        "scheme_id": source["scheme_id"],
        "scheme": scheme["name"],
        "category": scheme["category"],
        "last_checked": source["last_checked"],
    }


def chunk_text(
    text: str,
    source: Dict[str, object],
    scheme: Dict[str, object],
    max_chars: int = 700,
    overlap_chars: int = 100,
) -> List[Chunk]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks = []  # type: List[Chunk]
    current = []  # type: List[str]
    seen = set()
    metadata = _source_metadata(source, scheme)

    # Cap overlap to avoid infinite loops or full duplication in tiny max_chars tests
    actual_overlap = min(overlap_chars, max_chars // 3)

    def flush(lines_to_flush, overlap_lines):
        if not lines_to_flush:
            return overlap_lines
        chunk_text_value = "\n".join(lines_to_flush).strip()
        if not chunk_text_value:
            return overlap_lines
        key = (metadata["source_url"], _normalize_for_hash(chunk_text_value))
        
        if key not in seen:
            seen.add(key)
            digest = hashlib.sha1(("{0}|{1}".format(key[0], key[1])).encode("utf-8")).hexdigest()[:16]
            chunks.append(Chunk(id=digest, text=chunk_text_value, metadata=dict(metadata)))
        return list(overlap_lines)

    for i, line in enumerate(lines):
        pending_size = sum(len(part) for part in current) + len(current) + len(line)
        # If adding this line exceeds max, and it's not a header we're trying to keep together
        if current and pending_size > max_chars and not current[-1].startswith("#"):
            # Calculate overlap from current lines before flushing
            overlap_lines = []
            overlap_size = 0
            for l in reversed(current):
                if overlap_size + len(l) > actual_overlap:
                    break
                overlap_lines.insert(0, l)
                overlap_size += len(l) + 1
            current = flush(current, overlap_lines)
            
        current.append(line)

    flush(current, [])
    return chunks


def chunks_to_records(chunks: Iterable[Chunk]) -> List[Dict[str, object]]:
    return [{"id": chunk.id, "text": chunk.text, "metadata": chunk.metadata} for chunk in chunks]
