import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.retrieval.index import build_index, load_index
from pm_rag.core.retrieval.retriever import retrieve
from pm_rag.core.retrieval.keyword_search import keyword_search, tokenize_simple, bm25_score
from pm_rag.core.retrieval.reranker import rerank_by_scheme_and_source


def test_build_index_from_chunks():
    out = build_index()
    assert out.exists(), "index file not created"
    idx = load_index(str(out))
    assert "entries" in idx, "index missing entries key"
    assert idx["entries"], "index has no entries"
    assert "dim" in idx, "index missing dim key"


def test_keyword_search_returns_ranked_results():
    idx = load_index()
    entries = idx.get("entries", [])
    results = keyword_search("expense ratio", entries)
    assert results, "keyword search returned no results for 'expense ratio'"
    # results should be (idx, score) tuples with score > 0
    for idx_val, score in results:
        assert score > 0, f"score should be > 0, got {score}"


def test_embedding_search_returns_results():
    results = retrieve("expense ratio", top_k=3, use_keyword=False, use_faiss=True)
    assert results, "embedding search returned no results"
    for r in results:
        assert "source_url" in r, "result missing source_url"
        assert "metadata" in r, "result missing metadata"


def test_hybrid_retrieval_combines_keyword_and_embedding():
    results = retrieve("minimum sip amount", top_k=5, use_keyword=True, use_faiss=True)
    assert results, "hybrid retrieval returned no results"
    assert len(results) <= 5, "hybrid retrieval returned more than top_k results"
    # all results should have source_url and last_checked from corpus
    for r in results:
        assert r.get("source_url"), f"result missing source_url: {r}"
        assert r.get("last_checked"), f"result missing last_checked: {r}"
        assert r["source_url"] in [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        ], f"source_url not in corpus: {r['source_url']}"


def test_reranking_by_scheme():
    results = retrieve("exit load", top_k=10, target_scheme="ELSS")
    # should prefer ELSS scheme results higher
    assert results, "retrieval with target_scheme returned no results"
    top_schemes = [r["metadata"].get("scheme", "") for r in results[:3]]
    # at least one top result should mention ELSS or be from ELSS fund
    assert any("ELSS" in scheme for scheme in top_schemes), f"ELSS not prominent in top 3: {top_schemes}"


def test_retrieval_contract_metadata():
    results = retrieve("riskometer", top_k=3)
    assert results, "retrieval returned no results for 'riskometer'"
    for r in results:
        meta = r["metadata"]
        # check all required fields from ingestion are present
        assert "source_url" in meta, f"metadata missing source_url: {meta}"
        assert "scheme" in meta, f"metadata missing scheme: {meta}"
        assert "category" in meta, f"metadata missing category: {meta}"
        assert "last_checked" in meta, f"metadata missing last_checked: {meta}"
        assert "source_type" in meta, f"metadata missing source_type: {meta}"
        assert meta["source_type"] == "groww_scheme_page", "source_type must be groww_scheme_page"


def test_tokenize_simple():
    tokens = tokenize_simple("Expense Ratio: 0.75%")
    assert "expense" in tokens, "tokenize should lowercase"
    assert "ratio" in tokens
    assert "075" in tokens  # numeric part


def test_bm25_score_nonzero_for_matching_doc():
    query = ["expense", "ratio"]
    doc = ["expense", "ratio", "fee", "percentage"]
    score = bm25_score(query, doc)
    assert score > 0, "BM25 score should be > 0 for matching doc"


def test_bm25_score_zero_for_non_matching_doc():
    query = ["expense", "ratio"]
    doc = ["investment", "strategy", "growth"]
    score = bm25_score(query, doc)
    assert score == 0, "BM25 score should be 0 for non-matching doc"
