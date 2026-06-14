import json
from pathlib import Path
from typing import List, Dict, Optional

from pm_rag.core.retrieval.faiss_index import load_faiss_index, faiss_search
from pm_rag.core.retrieval.keyword_search import keyword_search
from pm_rag.core.retrieval.reranker import rerank_by_scheme_and_source
from pm_rag.core.retrieval.cross_encoder_reranker import cross_encoder_rerank


def retrieve(
    query: str,
    top_k: int = 5,
    index_dir: str = "data/indexes",
    use_faiss: bool = True,
    use_keyword: bool = True,
    use_cross_encoder: bool = True,
    target_scheme: Optional[str] = None,
) -> List[Dict]:
    """
    Hybrid retrieval: combines FAISS vector search, BM25 keyword search, and cross-encoder reranking.
    
    Architecture:
    1. FAISS: Dense retrieval using BGE embeddings (semantic similarity)
    2. BM25: Sparse retrieval using keyword matching (lexical similarity)
    3. Cross-encoder: Reranking for precision (query-document relevance)
    
    Args:
        query: user query string
        top_k: top results to return
        index_dir: path to FAISS index directory
        use_faiss: whether to use FAISS vector search
        use_keyword: whether to use BM25 keyword search
        use_cross_encoder: whether to use cross-encoder reranking
        target_scheme: optional scheme to boost in re-ranking
    
    Returns:
        List of result dicts with id, score, metadata, text, source_url, last_checked
    """
    scores_by_idx = {}  # type: Dict[int, float]
    
    # 1. FAISS Vector Search (Dense Retrieval)
    if use_faiss:
        try:
            index_data = load_faiss_index(index_dir)
            faiss_results = faiss_search(query, index_data, top_k=top_k * 2)
            
            for idx_pos, sim_score in faiss_results:
                # FAISS cosine similarity ranges [-1, 1], normalize to [0, 1]
                normalized_score = (sim_score + 1) / 2
                scores_by_idx[idx_pos] = scores_by_idx.get(idx_pos, 0) + normalized_score * 0.6
        except FileNotFoundError:
            print("Warning: FAISS index not found, skipping dense retrieval")
    
    # 2. BM25 Keyword Search (Sparse Retrieval)
    if use_keyword:
        try:
            # Load chunks for keyword search
            metadata_path = Path(index_dir) / "metadata.json"
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                entries = [
                    {
                        "text": text,
                        "metadata": meta,
                        "id": chunk_id,
                    }
                    for text, meta, chunk_id in zip(
                        metadata.get("texts", []),
                        metadata.get("metadatas", []),
                        metadata.get("chunk_ids", []),
                    )
                ]
                
                kw_results = keyword_search(query, entries)
                for idx_val, kw_score in kw_results:
                    scores_by_idx[idx_val] = scores_by_idx.get(idx_val, 0) + kw_score * 0.4
        except Exception as e:
            print(f"Warning: Keyword search failed: {e}")
    
    # 3. Convert to result dicts
    try:
        index_data = load_faiss_index(index_dir)
        results = []
        for idx_val, combined_score in scores_by_idx.items():
            meta = index_data["metadatas"][idx_val]
            text = index_data["texts"][idx_val]
            chunk_id = index_data["chunk_ids"][idx_val]
            
            results.append({
                "id": chunk_id,
                "score": combined_score,
                "metadata": meta,
                "text": text,
                "source_url": meta.get("source_url"),
                "last_checked": meta.get("last_checked"),
            })
    except Exception as e:
        print(f"Error building results: {e}")
        return []
    
    # 4. Cross-Encoder Reranking (if enabled and enough results)
    if use_cross_encoder and len(results) > 1:
        try:
            results = cross_encoder_rerank(query, results, top_k=top_k * 2)
        except Exception as e:
            print(f"Warning: Cross-encoder reranking failed, using rule-based reranking: {e}")
            results = rerank_by_scheme_and_source(results, target_scheme=target_scheme)
    else:
        # Fallback to rule-based reranking
        results = rerank_by_scheme_and_source(results, target_scheme=target_scheme)
    
    return results[:top_k]
