import os
import re
from typing import List, Dict, Tuple
from pm_rag.core.answering.prompts import build_prompt

# Optional Groq dependency
try:
    from groq import Groq
    _HAS_GROQ = True
except ImportError:
    _HAS_GROQ = False

from dotenv import load_dotenv
load_dotenv()

# Fund name keywords -> URL slug mapping for source attribution
_FUND_PATTERNS = [
    (re.compile(r'ELSS|Tax Saver', re.IGNORECASE), 'hdfc-elss-tax-saver'),
    (re.compile(r'Focused Fund', re.IGNORECASE), 'hdfc-focused-fund'),
    (re.compile(r'Mid[- ]Cap Fund', re.IGNORECASE), 'hdfc-mid-cap-fund'),
    (re.compile(r'Large[- ]Cap Fund', re.IGNORECASE), 'hdfc-large-cap-fund'),
    (re.compile(r'Equity Fund|Flexi Cap', re.IGNORECASE), 'hdfc-equity-fund'),
]


# Fallback: extract answer from chunks when LLM fails
# Chunk text uses \n as separator, so patterns use [\s\S] to match across lines
_FALLBACK_PATTERNS = {
    "expense": re.compile(r'Expense ratio\n([\d.]+%)', re.IGNORECASE),
    "ratio": re.compile(r'Expense ratio\n([\d.]+%)', re.IGNORECASE),
    "sip": re.compile(r'Min\. for SIP\n(₹[\d,]+)', re.IGNORECASE),
    "minimum": re.compile(r'Min\. for SIP\n(₹[\d,]+)', re.IGNORECASE),
    "exit": re.compile(r'[Ee]xit [Ll]oad\n?(?:of )?([\d.]+%[\s\S]*?)(?:\n\w|\Z)', re.IGNORECASE),
    "lock": re.compile(r'lock[- ]?in\s+period\n?(\d+\s*(?:year|month)s?)', re.IGNORECASE),
    "risk": re.compile(r'(Very High|High|Moderate|Low)\s*\n\s*Risk', re.IGNORECASE),
    "benchmark": re.compile(r'(?:Benchmark|benchmark)\n([^\n]+)', re.IGNORECASE),
    "type": re.compile(r'\n(Equity|Debt|Hybrid)\n(?:Mid Cap|Large Cap|Small Cap|Flexi Cap|ELSS)', re.IGNORECASE),
    "category": re.compile(r'\n(?:Equity|Debt|Hybrid)\n(Mid Cap|Large Cap|Small Cap|Flexi Cap|ELSS)', re.IGNORECASE),
}


def _extract_from_chunks(query: str, chunks: List[Dict]) -> str:
    """Extract answer from chunks when LLM returns 'not found'."""
    query_lower = query.lower()
    
    # Map query keywords to fallback pattern keys
    keyword_map = {
        "expense": "expense", "fee": "expense", "charge": "expense",
        "ratio": "ratio", "ter": "ratio",
        "sip": "sip", "minimum": "minimum", "min": "sip",
        "exit": "exit", "load": "exit", "redemption": "exit",
        "lock": "lock", "elss": "lock",
        "risk": "risk", "riskometer": "risk", "risky": "risk",
        "benchmark": "benchmark", "index": "benchmark",
        "type": "type", "category": "category", "kind": "type",
        "classify": "category", "classified": "category",
    }
    
    # Find the best matching pattern key
    pattern_key = None
    for kw in keyword_map:
        if kw in query_lower:
            pattern_key = keyword_map[kw]
            break
    
    if pattern_key and pattern_key in _FALLBACK_PATTERNS:
        pattern = _FALLBACK_PATTERNS[pattern_key]
        for chunk in chunks:
            text = chunk.get("text", "")
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                scheme = chunk.get("metadata", {}).get("scheme", "this fund")
                
                # Build a natural sentence based on the query type
                if pattern_key in ("expense", "ratio"):
                    return f"The {scheme} has an expense ratio of {value}."
                elif pattern_key in ("sip", "minimum"):
                    return f"The {scheme} has a minimum SIP investment of {value}."
                elif pattern_key == "exit":
                    return f"The {scheme} has an exit load of {value}."
                elif pattern_key == "lock":
                    return f"The {scheme} has a lock-in period of {value}."
                elif pattern_key == "risk":
                    return f"The {scheme} has a {value} risk level."
                elif pattern_key == "benchmark":
                    return f"The {scheme} tracks the {value}."
                elif pattern_key == "type":
                    return f"The {scheme} is an {value} mutual fund scheme."
                elif pattern_key == "category":
                    return f"The {scheme} is classified as a {value} fund."
                else:
                    return f"The {scheme}: {value}."
    
    return ""


def _match_source_url(answer: str, chunks: List[Dict]) -> Tuple[str, str]:
    """Match the fund mentioned in the answer to the correct source URL.
    
    Scans the answer for fund name keywords, then finds the chunk whose
    source_url matches that fund. Falls back to top chunk if no match.
    """
    for pattern, slug in _FUND_PATTERNS:
        if pattern.search(answer):
            for chunk in chunks:
                url = chunk.get("source_url", "") or chunk.get("metadata", {}).get("source_url", "")
                if slug in url:
                    last_checked = chunk.get("last_checked", "") or chunk.get("metadata", {}).get("last_checked", "")
                    return url, last_checked
    
    # Fallback to top chunk
    top = chunks[0] if chunks else {}
    meta = top.get("metadata", {})
    return (
        top.get("source_url", "") or meta.get("source_url", ""),
        top.get("last_checked", "") or meta.get("last_checked", ""),
    )


def generate_answer(query: str, retrieved_chunks: List[Dict]) -> Tuple[str, str, str]:
    """
    Generates an answer using Groq LLM API.
    Returns: (raw_answer_text, source_url, last_checked)
    """
    if not retrieved_chunks:
        return "Information not found in the fixed Groww corpus.", "", ""
        
    prompt = build_prompt(query, retrieved_chunks)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not _HAS_GROQ or not api_key:
        # Fallback simulator for tests running without an API key or missing groq
        top_chunk = retrieved_chunks[0]
        text = top_chunk.get("text", "")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
        raw_answer = sentences[0] if sentences else "Information not found in the fixed Groww corpus."
    else:
        try:
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150,
            )
            raw_answer = completion.choices[0].message.content
        except Exception as e:
            raw_answer = f"Error during generation: {str(e)}"
    
    # If LLM returned "not found", try extracting from chunks directly
    if "information not found" in raw_answer.lower() or "not found" in raw_answer.lower():
        extracted = _extract_from_chunks(query, retrieved_chunks)
        if extracted:
            raw_answer = extracted
    
    # Match source URL to the fund mentioned in the answer
    source_url, last_checked = _match_source_url(raw_answer, retrieved_chunks)
    
    return raw_answer, source_url, last_checked
