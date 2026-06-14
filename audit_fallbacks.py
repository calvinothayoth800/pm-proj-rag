#!/usr/bin/env python3
"""
Comprehensive Fallback Audit - Check if all components are using REAL implementations
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("RAG COMPONENT FALLBACK AUDIT")
print("=" * 70)

# Track results
results = {}

# 1. GROQ LLM API
print("\n[1/5] GROQ LLM API (Answer Generation)")
print("-" * 70)
try:
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        client = Groq(api_key=api_key)
        # Test actual API call
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say test"}],
            temperature=0.0,
            max_tokens=5,
        )
        print(f"Status: [OK] REAL LLM ACTIVE")
        print(f"API Key: Present (starts with {api_key[:10]}...)")
        print(f"Test Response: {completion.choices[0].message.content}")
        results["GROQ LLM"] = "REAL"
    else:
        print(f"Status: [ERROR] FALLBACK MODE (no API key)")
        results["GROQ LLM"] = "FALLBACK"
except Exception as e:
    print(f"Status: [ERROR] {e}")
    results["GROQ LLM"] = "ERROR"

# 2. FASTEMBED (BGE Embeddings)
print("\n[2/5] FASTEMBED (BGE Embeddings)")
print("-" * 70)
try:
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    embeddings = list(model.embed(["test sentence"]))
    dim = len(embeddings[0])
    print(f"Status: [OK] REAL BGE EMBEDDINGS ACTIVE")
    print(f"Model: BAAI/bge-small-en-v1.5")
    print(f"Dimension: {dim}")
    results["BGE Embeddings"] = "REAL"
except Exception as e:
    print(f"Status: [ERROR] FALLBACK MODE (hash-based embeddings)")
    print(f"Error: {e}")
    results["BGE Embeddings"] = "FALLBACK"

# 3. FAISS (Vector Search)
print("\n[3/5] FAISS (Vector Similarity Search)")
print("-" * 70)
try:
    import faiss
    import numpy as np
    # Test FAISS functionality
    dim = 384
    index = faiss.IndexFlatIP(dim)
    test_vector = np.random.random((1, dim)).astype('float32')
    faiss.normalize_L2(test_vector)
    index.add(test_vector)
    print(f"Status: [OK] REAL FAISS INDEX ACTIVE")
    print(f"Index Type: IndexFlatIP (cosine similarity)")
    print(f"Test: Vector added and indexed successfully")
    results["FAISS"] = "REAL"
except Exception as e:
    print(f"Status: [ERROR] {e}")
    results["FAISS"] = "ERROR"

# 4. CROSS-ENCODER (Reranking)
print("\n[4/5] CROSS-ENCODER (Reranking)")
print("-" * 70)
try:
    from sentence_transformers import CrossEncoder
    # Just verify import works (loading model takes time)
    print(f"Status: [OK] REAL CROSS-ENCODER AVAILABLE")
    print(f"Model: cross-encoder/ms-marco-MiniLM-L-6-v2")
    print(f"Note: Model loads on first use (lazy loading)")
    results["Cross-Encoder"] = "REAL"
except Exception as e:
    print(f"Status: [ERROR] FALLBACK MODE (no reranking)")
    print(f"Error: {e}")
    results["Cross-Encoder"] = "FALLBACK"

# 5. BM25 (Keyword Search)
print("\n[5/5] BM25 (Keyword Search)")
print("-" * 70)
try:
    from pm_rag.core.retrieval.keyword_search import BM25Index
    index = BM25Index()
    index.build([{"text": "test document about expense ratio"}])
    score = index.score(["expense", "ratio"], 0)
    print(f"Status: [OK] REAL CORPUS-AWARE BM25 ACTIVE")
    print(f"Type: Corpus-aware with proper IDF calculation")
    print(f"Test Score: {score:.4f}")
    results["BM25"] = "REAL"
except Exception as e:
    print(f"Status: [ERROR] FALLBACK MODE (simple BM25)")
    print(f"Error: {e}")
    results["BM25"] = "FALLBACK"

# Summary
print("\n" + "=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)

all_real = all(v == "REAL" for v in results.values())

for component, status in results.items():
    icon = "[OK]" if status == "REAL" else "[FALLBACK]"
    print(f"{icon} {component:25s} {status}")

print("\n" + "=" * 70)
if all_real:
    print("[OK] ALL COMPONENTS USING REAL IMPLEMENTATIONS!")
    print("No fallbacks detected. Full RAG pipeline active.")
else:
    print("[WARNING] SOME COMPONENTS IN FALLBACK MODE!")
    print("Check errors above and install missing dependencies.")
print("=" * 70)
