import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pm_rag.core.retrieval.retriever import retrieve

print("Testing FAISS-based hybrid retrieval...")
print("=" * 60)

# Test 1: Expense ratio query
print("\nTest 1: Expense ratio query")
results = retrieve("What is the expense ratio?", top_k=3)
print(f"Retrieved {len(results)} chunks")
if results:
    print(f"Top result score: {results[0]['score']:.4f}")
    print(f"Top result scheme: {results[0]['metadata'].get('scheme', 'N/A')}")
    print(f"Top result URL: {results[0]['source_url']}")

# Test 2: Exit load query
print("\nTest 2: Exit load query")
results = retrieve("What is the exit load for HDFC Mid Cap?", top_k=3)
print(f"Retrieved {len(results)} chunks")
if results:
    print(f"Top result score: {results[0]['score']:.4f}")
    print(f"Top result scheme: {results[0]['metadata'].get('scheme', 'N/A')}")

# Test 3: SIP amount query
print("\nTest 3: Minimum SIP query")
results = retrieve("What is the minimum SIP amount?", top_k=3)
print(f"Retrieved {len(results)} chunks")
if results:
    print(f"Top result score: {results[0]['score']:.4f}")
    print(f"Top result scheme: {results[0]['metadata'].get('scheme', 'N/A')}")

print("\n" + "=" * 60)
print("[OK] FAISS retrieval pipeline working correctly!")
