from typing import List, Dict

# Optional sentence-transformers dependency for cross-encoder
try:
    from sentence_transformers import CrossEncoder
    _HAS_CROSS_ENCODER = True
except ImportError:
    _HAS_CROSS_ENCODER = False


_cross_encoder_model = None


def _get_cross_encoder_model():
    """Lazy load cross-encoder model."""
    global _cross_encoder_model
    if _cross_encoder_model is None:
        if not _HAS_CROSS_ENCODER:
            raise ImportError("sentence-transformers is not installed")
        # ms-marco-MiniLM-L-6-v2 is fast and accurate for reranking
        _cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _cross_encoder_model


def cross_encoder_rerank(
    query: str,
    results: List[Dict],
    top_k: int = 5,
) -> List[Dict]:
    """
    Rerank retrieval results using cross-encoder model.
    
    Cross-encoders process query-document pairs jointly, providing more accurate
    relevance scores than bi-encoders (embeddings) at the cost of speed.
    
    This is the standard reranking approach in production RAG systems:
    1. Bi-encoder (FAISS embeddings): Fast retrieval of top 50-100 candidates
    2. Cross-encoder: Precise reranking of candidates to top 5-10
    
    Args:
        query: User query
        results: Retrieved chunks from hybrid search
        top_k: Number of results to return after reranking
    
    Returns:
        Reranked list of result dicts with updated scores
    """
    if not _HAS_CROSS_ENCODER:
        raise ImportError("sentence-transformers not available for cross-encoder reranking")
    
    model = _get_cross_encoder_model()
    
    # Create query-document pairs
    pairs = [(query, result["text"]) for result in results]
    
    # Get relevance scores from cross-encoder
    scores = model.predict(pairs, show_progress_bar=False)
    
    # Update scores in results
    for i, result in enumerate(results):
        # Combine original hybrid score with cross-encoder score
        # Cross-encoder scores can be any real number, typically [-10, 10] for ms-marco
        cross_score = float(scores[i])
        original_score = result.get("score", 0)
        
        # Weight cross-encoder more heavily (it's more accurate)
        result["rerank_score"] = original_score * 0.3 + cross_score * 0.7
        result["cross_encoder_score"] = cross_score
    
    # Sort by rerank score
    results_sorted = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
    
    # Clean up temporary scores
    for r in results_sorted:
        if "rerank_score" in r:
            r["score"] = r.pop("rerank_score")
        if "cross_encoder_score" in r:
            del r["cross_encoder_score"]
    
    return results_sorted[:top_k]
