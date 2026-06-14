from typing import List

# We try to import fastembed. If it fails (e.g. during some local tests on old python), we fall back.
try:
    from fastembed import TextEmbedding
    _HAS_FASTEMBED = True
except ImportError:
    _HAS_FASTEMBED = False

_model = None

def _get_model():
    global _model
    if _model is None:
        if not _HAS_FASTEMBED:
            raise ImportError("fastembed is not installed or available.")
        _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _model


def embed_text(text: str, dim: int = 384) -> List[float]:
    if not _HAS_FASTEMBED:
        # Fallback for testing on old python without fastembed
        import hashlib, math
        import re
        vec = [0.0] * dim
        for token in re.findall(r"\w+", text.lower()):
            h = hashlib.md5(token.encode("utf-8")).hexdigest()
            idx = int(h, 16) % dim
            sign = 1.0 if (int(h[-1], 16) % 2 == 0) else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm > 0 else vec

    model = _get_model()
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()


def embed_texts(texts: List[str], dim: int = 384) -> List[List[float]]:
    if not _HAS_FASTEMBED:
        return [embed_text(t, dim) for t in texts]
        
    model = _get_model()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]
