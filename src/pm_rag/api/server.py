import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pm_rag.core.retrieval.retriever import retrieve
from pm_rag.core.compliance.classifier import classify_query_intent, detect_sensitive_data
from pm_rag.core.answering.generator import generate_answer
from pm_rag.core.answering.formatter import format_final_response

app = FastAPI(title="PM RAG API")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    source_url: str
    last_updated: str
    intent: str

# Serve UI from the static directory
ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui")

@app.post("/api/chat", response_model=QueryResponse)
def chat_endpoint(request: QueryRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Check for sensitive data first
    has_sensitive, pattern = detect_sensitive_data(query)
    if has_sensitive:
        return QueryResponse(
            answer="I cannot provide personal or sensitive information. I can only answer factual questions about mutual funds.",
            source_url="",
            last_updated="",
            intent="sensitive_data"
        )
    
    # 2. Classify Intent
    intent = classify_query_intent(query)
    
    # 3. Handle compliance refusals
    if intent in ["investment_advice", "comparison", "ranking", "return_projection", "performance_calculation"]:
        return QueryResponse(
            answer="I cannot provide investment advice, comparisons, or projections. I can only answer factual questions about mutual funds.",
            source_url="",
            last_updated="",
            intent=intent
        )

    # 4. Retrieve
    chunks = retrieve(query, top_k=5)
    
    # 5. Generate Answer
    raw_answer, src_url, last_checked = generate_answer(query, chunks)
    
    # 6. Format to exact contract
    final_text = format_final_response(raw_answer, src_url, last_checked)
    
    return QueryResponse(
        answer=final_text,
        source_url=src_url,
        last_updated=last_checked,
        intent=intent
    )

# Ensure ui directory exists for mounting
os.makedirs(ui_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=ui_dir), name="static")

@app.get("/")
def serve_ui():
    index_path = os.path.join(ui_dir, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_path)
