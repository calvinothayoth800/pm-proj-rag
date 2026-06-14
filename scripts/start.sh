#!/bin/bash
# Startup script for Hugging Face Spaces
# Builds FAISS index on first run if it doesn't exist

echo "Starting RAG Assistant..."

# Check if FAISS index exists
if [ ! -f "data/indexes/faiss_index.bin" ]; then
    echo "FAISS index not found. Building..."
    python scripts/ingest.py
    python scripts/build_index.py
    echo "Index built successfully!"
else
    echo "FAISS index found. Loading..."
fi

# Start the FastAPI server
echo "Starting server on port 7860..."
uvicorn src.pm_rag.api.server:app --host 0.0.0.0 --port 7860
