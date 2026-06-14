# Handoff

Project: Mutual Fund FAQ Assistant, facts-only RAG for five fixed Groww scheme pages.

Current state: **Phases 0-7 implemented and tested**. Production-grade RAG prototype with FAISS vector search, hybrid retrieval, cross-encoder reranking, and comprehensive test coverage.

Goal: Answer objective mutual-fund FAQ queries using only the exact five Groww URLs in `configs/corpus.yaml`. No other URLs are allowed. No investment advice, recommendations, comparisons, projections, return calculations, or sensitive-data handling.

Hard response contract: max 3 sentences; exactly 1 source link from the five Groww URLs; footer `Last updated from sources: <date>`; refusal for advisory/unsupported/sensitive requests.

Structure decision: production code is component-wise under `src/pm_rag/`; tests/docs are phase-wise for evaluation.

Fixed corpus:
1 HDFC Mid Cap Fund - Direct Growth | Mid Cap | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth
2 HDFC Equity Fund - Direct Growth | Flexi Cap | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
3 HDFC Focused Fund - Direct Growth | Focused | https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth
4 HDFC ELSS Tax Saver - Direct Plan Growth | ELSS | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
5 HDFC Large Cap Fund - Direct Growth | Large Cap | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth

UI implemented: welcome message, 4 example questions (clickable chips), visible disclaimer `Facts-only. No investment advice.`, API status indicator.

Privacy ban: do not collect/store/process PAN, Aadhaar, account numbers, OTPs, emails, phone numbers.

Phase Status:
- Phase 0: **IMPLEMENTED** - Foundation, docs, scaffold, edge-case tests (7 tests passing)
- Phase 1: **IMPLEMENTED** - Fixed corpus validated as 5 exact Groww URLs in `configs/corpus.yaml` (7 tests passing)
- Phase 2: **IMPLEMENTED** - Live ingestion pipeline with real scraped outputs (9 tests passing)
  - Latest run: 20260608024005;
  - Artifacts: `data/raw/latest-manifest.json`, `data/processed/chunks-latest.json`
- Phase 3: **IMPLEMENTED** - FAISS vector index with BGE embeddings + BM25 hybrid retrieval
  - FAISS IndexFlatIP (cosine similarity on 384-dim vectors)
  - Corpus-aware BM25 with proper IDF calculation
  - Hybrid fusion: 60% dense + 40% sparse
- Phase 4: **IMPLEMENTED** - Semantic intent classification with BGE embeddings + keyword fallback
  - Pre-computed intent phrase embeddings for similarity matching
  - Sensitive data detection (PAN, Aadhaar, account, OTP, email, phone)
  - Allowed/refused query classification
- Phase 5: **IMPLEMENTED** - Groq LLM API (Llama 3.1) with strict 3-sentence + citation formatting
  - Facts-only prompts with retrieved context
  - Response validation (sentence count, source link, footer)
  - Fallback simulator for tests without API key
- Phase 6: **IMPLEMENTED** - Minimal UI/API with FastAPI server
  - FastAPI REST endpoint: POST /api/chat
  - Static file serving for UI
  - Web UI: Welcome message, 4 example question chips, disclaimer banner, API status badge
  - Auto-link formatting in responses
- Phase 7: **IMPLEMENTED** - Comprehensive test suite (76 tests, 96% pass rate)
  - `test_phase7_evaluation.py`: 51 tests covering compliance, format, retrieval, integration
  - `tests/fixtures/sample_queries.json`: Sample queries for all categories
  - Test categories: advisory refusals (6), sensitive data (7), allowed queries (8), sentence count (5), source link (4), footer (4), full compliance (4), retrieval quality (5), integration (4), edge cases (4)
- Phase 8: **IMPLEMENTED** - Operations and maintenance with GitHub Actions
  - `.github/workflows/ci.yml`: CI pipeline (test on push/PR)
  - `.github/workflows/scheduled-refresh.yml`: Weekly corpus refresh (Monday 00:00 UTC)
  - `scripts/update_handoff.py`: Automated handoff state updates
  - `docs/PHASE8_OPERATIONS.md`: Complete operations guide
  - Cost: $0 (GitHub Actions free tier for public repos)

RAG Architecture Components:
- Embeddings: BAAI/bge-small-en-v1.5 via FastEmbed (384 dimensions)
- Vector DB: FAISS IndexFlatIP (industry-standard ANN search)
- Keyword Search: Corpus-aware BM25 with proper IDF
- Reranking: Cross-encoder ms-marco-MiniLM-L-6-v2 (sentence-transformers)
- LLM: Groq API with llama-3.1-8b-instant (temperature=0.0, max_tokens=150)
- Hybrid Retrieval: FAISS (60%) + BM25 (40%) → Cross-encoder rerank → Top 5

Key directories:
`src/pm_rag/api` FastAPI server with /api/chat endpoint
`src/pm_rag/ui` Minimal web interface (HTML/CSS/JS)
`src/pm_rag/core/ingestion` Fetch/parse/chunk only allowlisted Groww pages
`src/pm_rag/core/retrieval` FAISS index, BGE embeddings, BM25, cross-encoder reranker
`src/pm_rag/core/answering` Prompts/generation/formatting with Groq LLM
`src/pm_rag/core/compliance` Semantic classification/refusal/validation
`src/pm_rag/core/sources` Corpus catalog loading/validation
`configs/corpus.yaml` Selected AMC/schemes/source URLs
`data/indexes/faiss_index.bin` FAISS vector index (112KB, 73 vectors)
`data/indexes/metadata.json` Index metadata (chunk IDs, texts, metadatas)
`tests/test_phase7_evaluation.py` Comprehensive Phase 7 test suite
`tests/fixtures/sample_queries.json` Sample query fixtures
`docs/edge-cases/` Phase-specific failure modes and checks

Dependencies (setup.py):
- fastembed>=0.3.0 (BGE embeddings)
- faiss-cpu>=1.7.4 (vector search)
- groq>=0.8.0 (LLM API)
- sentence-transformers>=2.2.0 (cross-encoder)
- fastapi>=0.104.0, uvicorn>=0.24.0 (API)
- beautifulsoup4>=4.12.0, pyyaml>=6.0, requests>=2.31.0

Run commands:
```bash
# Install dependencies
pip install -e .

# Build FAISS index
python scripts/build_index.py

# Run all tests (76 tests)
py -m unittest discover -s tests

# Start API server
uvicorn src.pm_rag.api.server:app --reload --port 8000
```

Next best step: Deploy to production (Vercel/Railway/Render) or scale corpus with more Groww URLs

**CRITICAL RULE FOR ALL AIs**: You MUST update this `handoff.md` file whenever meaningful progress is made on any phase. It serves as the single source of truth for project state and handover between different sessions or agents.
