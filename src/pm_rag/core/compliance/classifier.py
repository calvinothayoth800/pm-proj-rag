import re
from typing import Tuple

from pm_rag.core.compliance.policies import (
    ALLOWED_QUERY_INTENTS,
    REFUSED_QUERY_INTENTS,
    SENSITIVE_DATA_PATTERNS,
)

from pm_rag.core.retrieval.embedder import embed_text

# Semantic intent classification using embedding similarity
# Each intent has representative phrases for semantic matching
INTENT_PHRASES = {
    "investment_advice": [
        "should i invest in this fund",
        "is this a good investment",
        "recommend me a mutual fund",
        "what should i buy",
        "is it wise to invest",
        "where should i put my money",
        "best fund to invest",
    ],
    "comparison": [
        "which fund is better",
        "which is better",
        "compare these funds",
        "fund a vs fund b",
        "difference between funds",
        "which one is good",
        "fund a or fund b",
    ],
    "ranking": [
        "rank these funds",
        "best performing fund",
        "top mutual funds",
        "highest return fund",
        "which is number one",
    ],
    "return_projection": [
        "what will be my return",
        "future returns expected",
        "how much will i earn",
        "project my returns",
        "expected profit",
    ],
    "performance_calculation": [
        "calculate my profit",
        "calculate returns",
        "compute my gains",
        "what is my roi",
        "sip calculator",
    ],
    "expense_ratio": [
        "what is the expense ratio",
        "fund fees",
        "management charges",
        "ter ratio",
        "expense percentage",
    ],
    "exit_load": [
        "what is the exit load",
        "penalty for withdrawal",
        "early redemption fee",
        "exit charges",
    ],
    "minimum_sip": [
        "minimum sip amount",
        "smallest investment",
        "start sip with",
        "minimum investment",
    ],
    "lock_in_period": [
        "lock in period",
        "elss lock-in",
        "when can i withdraw",
        "withdrawal restrictions",
    ],
    "riskometer": [
        "what is the risk",
        "risk level",
        "riskometer",
        "how risky is this",
    ],
    "benchmark": [
        "benchmark index",
        "what does it track",
        "benchmark fund",
    ],
    "document_download": [
        "download statement",
        "tax statement",
        "capital gains report",
        "how to get documents",
    ],
    "factual_question": [
        "tell me about mutual funds",
        "what is a mutual fund",
        "how do mutual funds work",
        "what about this fund",
        "tell me about this",
        "fund information",
        "fund details",
    ],
}

# Precompute embeddings for intent phrases
_intent_embeddings_cache = {}


def _get_intent_embeddings():
    """Lazy load and cache intent phrase embeddings."""
    if not _intent_embeddings_cache:
        for intent, phrases in INTENT_PHRASES.items():
            _intent_embeddings_cache[intent] = []
            for phrase in phrases:
                try:
                    emb = embed_text(phrase)
                    _intent_embeddings_cache[intent].append((phrase, emb))
                except Exception:
                    pass  # Skip if embedding fails
    return _intent_embeddings_cache


def _cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def classify_query_intent(query: str) -> str:
    """
    Classify query intent using semantic similarity with embedding fallback.
    
    Architecture:
    1. Semantic matching using BGE embeddings (primary)
    2. Keyword matching (fallback if embeddings unavailable)
    
    Args:
        query: User query string
    
    Returns:
        Intent classification string
    """
    query_lower = query.lower()
    
    # 1. Try semantic classification using embeddings
    try:
        q_emb = embed_text(query)
        intent_embeddings = _get_intent_embeddings()
        
        best_intent = None
        best_score = 0.0
        threshold = 0.75  # Lower threshold for better recall
        
        for intent, phrase_embeddings in intent_embeddings.items():
            for phrase, p_emb in phrase_embeddings:
                sim = _cosine_similarity(q_emb, p_emb)
                if sim > best_score:
                    best_score = sim
                    best_intent = intent
        
        # If semantic match is strong enough, use it
        if best_score > threshold and best_intent:
            return best_intent
    
    except Exception:
        pass  # Fallback to keyword matching
    
    # 2. Keyword-based classification (fallback)
    # Check vague/informational patterns first (prevent false positive on advice)
    if any(x in query_lower for x in ["tell me about", "what about", "what is a", "what are", "how do"]):
        if not any(x in query_lower for x in ["should", "better", "best", "recommend", "compare"]):
            return "factual_question"
    
    # Check refused patterns first (safety priority)
    if any(x in query_lower for x in ["should i invest", "which fund", "which is better", "better fund", "recommend", "is it wise", "should i buy"]):
        return "investment_advice"
    
    if any(x in query_lower for x in ["compare", "comparison", "vs", "versus", "better than", "difference between", "which is better", "or hdfc"]):
        return "comparison"
    
    if any(x in query_lower for x in ["rank", "best", "top", "highest return", "number one"]):
        return "ranking"
    
    if any(x in query_lower for x in ["project", "future", "expect", "will return", "will earn"]):
        return "return_projection"
    
    if any(x in query_lower for x in ["calculate", "compute", "roi", "profit", "gains"]):
        return "performance_calculation"
    
    # Check allowed patterns
    if any(x in query_lower for x in ["expense", "ratio", "fee", "charges", "ter"]):
        return "expense_ratio"
    
    if any(x in query_lower for x in ["exit", "load", "withdrawal fee", "redemption"]):
        return "exit_load"
    
    if any(x in query_lower for x in ["minimum", "sip amount", "smallest", "start sip"]):
        return "minimum_sip"
    
    if any(x in query_lower for x in ["lock", "elss", "withdraw", "when can i"]):
        return "lock_in_period"
    
    if any(x in query_lower for x in ["risk", "riskometer", "risky", "risk level"]):
        return "riskometer"
    
    if any(x in query_lower for x in ["benchmark", "index", "track"]):
        return "benchmark"
    
    if any(x in query_lower for x in ["download", "statement", "tax", "capital gains", "document"]):
        return "document_download"
    
    return "factual_question"


def detect_sensitive_data(query: str) -> Tuple[bool, str]:
    """
    Detect if query contains requests for sensitive data.
    Returns (has_sensitive, pattern_found).
    """
    query_lower = query.lower()
    for pattern in SENSITIVE_DATA_PATTERNS:
        if pattern in query_lower:
            return True, pattern
    return False, ""


def is_allowed_query(query: str) -> Tuple[bool, str]:
    """
    Determine if query is allowed. Returns (is_allowed, reason).
    """
    has_sensitive, pattern = detect_sensitive_data(query)
    if has_sensitive:
        return False, f"contains sensitive data request ({pattern})"
    
    intent = classify_query_intent(query)
    if intent in REFUSED_QUERY_INTENTS:
        return False, f"query type not allowed: {intent}"
    
    return True, ""
