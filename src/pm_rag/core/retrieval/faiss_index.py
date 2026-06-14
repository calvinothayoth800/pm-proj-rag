import json
import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

from pm_rag.core.retrieval.embedder import embed_text, embed_texts


def build_faiss_index(
    processed_path: str = "data/processed/chunks-latest.json",
    index_dir: str = "data/indexes",
    model_name: str = "BAAI/bge-small-en-v1.5",
) -> Path:
    """
    Build FAISS vector index from processed chunks.
    
    Uses FAISS IndexFlatIP (inner product) for cosine similarity on normalized vectors.
    For larger corpora (>100K docs), would use IndexIVFFlat or IndexHNSW.
    
    Args:
        processed_path: Path to processed chunks JSON
        index_dir: Directory to save FAISS index and metadata
        model_name: Embedding model name for reference
    
    Returns:
        Path to saved index directory
    """
    proc = Path(processed_path)
    assert proc.exists(), f"Processed chunks not found at {processed_path}"
    
    payload = json.loads(proc.read_text(encoding="utf-8"))
    chunks = payload.get("chunks", [])
    
    if not chunks:
        raise ValueError("No chunks found in processed data")
    
    # Extract texts and metadata
    texts = [chunk.get("text", "") for chunk in chunks]
    metadatas = [chunk.get("metadata", {}) for chunk in chunks]
    chunk_ids = [chunk.get("id", "") for chunk in chunks]
    
    # Generate embeddings
    print(f"Embedding {len(texts)} chunks with {model_name}...")
    embeddings = embed_texts(texts)
    
    # Convert to numpy array
    vectors = np.array(embeddings).astype('float32')
    dim = vectors.shape[1]
    
    # Normalize vectors for cosine similarity (FAISS inner product = cosine on normalized)
    faiss.normalize_L2(vectors)
    
    # Build FAISS index
    # IndexFlatIP: Exact search using inner product (equivalent to cosine similarity for normalized vectors)
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    
    print(f"FAISS index built: {index.ntotal} vectors, {dim} dimensions")
    
    # Save index and metadata
    idx_dir = Path(index_dir)
    idx_dir.mkdir(parents=True, exist_ok=True)
    
    # Save FAISS index
    faiss_path = idx_dir / "faiss_index.bin"
    faiss.write_index(index, str(faiss_path))
    
    # Save metadata separately (FAISS only stores vectors)
    metadata = {
        "model_name": model_name,
        "dim": dim,
        "num_vectors": index.ntotal,
        "chunk_ids": chunk_ids,
        "metadatas": metadatas,
        "texts": texts,
    }
    metadata_path = idx_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"Index saved to: {faiss_path}")
    print(f"Metadata saved to: {metadata_path}")
    
    return idx_dir


def load_faiss_index(index_dir: str = "data/indexes") -> Dict:
    """
    Load FAISS index and associated metadata.
    
    Returns:
        Dict with 'index' (FAISS index), 'metadata' (chunk metadata), 'texts' (chunk texts)
    """
    idx_dir = Path(index_dir)
    
    faiss_path = idx_dir / "faiss_index.bin"
    metadata_path = idx_dir / "metadata.json"
    
    if not faiss_path.exists():
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Index metadata not found at {metadata_path}")
    
    # Load FAISS index
    index = faiss.read_index(str(faiss_path))
    
    # Load metadata
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    
    return {
        "index": index,
        "model_name": metadata.get("model_name", "BAAI/bge-small-en-v1.5"),
        "dim": metadata.get("dim", 384),
        "chunk_ids": metadata.get("chunk_ids", []),
        "metadatas": metadata.get("metadatas", []),
        "texts": metadata.get("texts", []),
    }


def faiss_search(
    query: str,
    index_data: Dict,
    top_k: int = 5,
) -> List[Tuple[int, float]]:
    """
    Search FAISS index for similar vectors.
    
    Args:
        query: Query text
        index_data: Loaded index data from load_faiss_index()
        top_k: Number of results to return
    
    Returns:
        List of (index_position, similarity_score) tuples
    """
    index = index_data["index"]
    
    # Embed query
    query_emb = embed_text(query)
    query_vector = np.array([query_emb]).astype('float32')
    faiss.normalize_L2(query_vector)
    
    # Search
    scores, indices = index.search(query_vector, top_k)
    
    # Return as list of tuples
    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx != -1:  # FAISS returns -1 for empty slots
            results.append((int(idx), float(score)))
    
    return results


def build_and_save_index(processed_path: str = "data/processed/chunks-latest.json", index_dir: str = "data/indexes") -> Path:
    """Backwards-compatible wrapper for old build_index interface"""
    return build_faiss_index(processed_path, index_dir)
