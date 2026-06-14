import math
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple


class BM25Index:
    """
    Corpus-aware BM25 index with proper IDF calculation.
    
    Standard BM25 formula:
    score(D, Q) = sum(IDF(q_i) * (f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * |D|/avgdl)))
    
    Where:
    - IDF(q_i) = log((N - n(q_i) + 0.5) / (n(q_i) + 0.5))
    - f(q_i, D) = term frequency in document
    - N = total documents
    - n(q_i) = documents containing term
    - avgdl = average document length
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []  # type: List[List[str]]
        self.doc_freq = defaultdict(int)  # term -> number of docs containing it
        self.avg_doc_len = 0.0
    
    def build(self, documents: List[Dict[str, str]]):
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of dicts with 'text' key
        """
        self.documents = []
        self.doc_freq = defaultdict(int)
        
        # Tokenize all documents
        for doc in documents:
            text = doc.get("text", "")
            tokens = tokenize_simple(text)
            self.documents.append(tokens)
            
            # Update document frequency
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freq[token] += 1
        
        # Calculate average document length
        if self.documents:
            self.avg_doc_len = sum(len(doc) for doc in self.documents) / len(self.documents)
    
    def idf(self, term: str) -> float:
        """Calculate IDF for a term."""
        N = len(self.documents)
        n = self.doc_freq.get(term, 0)
        # Standard BM25 IDF
        return math.log((N - n + 0.5) / (n + 0.5) + 1.0)
    
    def score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Calculate BM25 score for a query against a document."""
        if doc_idx >= len(self.documents):
            return 0.0
        
        doc_tokens = self.documents[doc_idx]
        doc_len = len(doc_tokens)
        doc_counter = Counter(doc_tokens)
        
        score = 0.0
        for q_token in query_tokens:
            if q_token in doc_counter:
                tf = doc_counter[q_token]
                idf = self.idf(q_token)
                
                # BM25 term score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
                score += idf * (numerator / denominator)
        
        return score


_bm25_index = None


def tokenize_simple(text: str) -> List[str]:
    """Simple tokenizer: lowercase, remove punctuation, split."""
    text = re.sub(r"[^\w\s]", "", text.lower())
    return text.split()


def bm25_score(query_tokens: List[str], doc_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> float:
    """
    Legacy BM25 score function (backwards compatibility).
    For corpus-aware search, use BM25Index class instead.
    """
    query_counter = Counter(query_tokens)
    doc_counter = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    avg_len = max(doc_len, 100)  # avoid division by zero
    score = 0.0
    for q_token, q_freq in query_counter.items():
        if q_token in doc_counter:
            doc_freq = doc_counter[q_token]
            # Approximate IDF (not corpus-aware)
            idf = math.log(1 + (1 - doc_freq + 0.5) / (doc_freq + 0.5))
            norm_len = 1 - b + b * (doc_len / avg_len)
            score += idf * ((k1 + 1) * doc_freq) / (k1 * norm_len + doc_freq)
    return score


def keyword_search(query: str, documents: List[Dict]) -> List[Tuple[int, float]]:
    """
    Keyword search using BM25.
    Uses corpus-aware BM25 if available, falls back to simple BM25.
    
    Args:
        query: Query string
        documents: List of document dicts with 'text' key
    
    Returns:
        List of (doc_index, score) tuples
    """
    query_tokens = tokenize_simple(query)
    
    # Try to use corpus-aware BM25
    global _bm25_index
    if _bm25_index is None or len(_bm25_index.documents) != len(documents):
        try:
            _bm25_index = BM25Index()
            _bm25_index.build(documents)
        except Exception:
            _bm25_index = None  # Fallback to simple BM25
    
    scores = []
    for idx, doc in enumerate(documents):
        if _bm25_index is not None:
            # Use corpus-aware BM25
            bm25 = _bm25_index.score(query_tokens, idx)
        else:
            # Fallback to simple BM25
            text = doc.get("text", "")
            doc_tokens = tokenize_simple(text)
            bm25 = bm25_score(query_tokens, doc_tokens)
        
        # Bonus for metadata keywords (scheme matching)
        meta = doc.get("metadata", {})
        scheme = str(meta.get("scheme", "")).lower()
        for q_token in query_tokens:
            if q_token in scheme:
                bm25 += 5.0
        
        if bm25 > 0:
            scores.append((idx, bm25))
    
    return scores
