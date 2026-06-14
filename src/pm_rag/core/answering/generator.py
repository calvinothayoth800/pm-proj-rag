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
_FALLBACK_PATTERNS = {
    "expense": re.compile(r'expense\s+ratio[^.]*\d+\.?\d*\s*%', re.IGNORECASE),
    "ratio": re.compile(r'(?:expense|fee|charge)[^.]*\d+\.?\d*\s*%', re.IGNORECASE),
    "sip": re.compile(r'(?:minimum|minimum\s+SIP|SIP\s+Investment)[^.]*₹\s*\d+', re.IGNORECASE),
    "minimum": re.compile(r'(?:minimum|smallest)[^.]*₹\s*\d+', re.IGNORECASE),
    "exit": re.compile(r'exit\s+load[^.]*\d+\.?\d*\s*%', re.IGNORECASE),
    "load": re.compile(r'(?:exit|redemption)[^.]*\d+\.?\d*\s*%', re.IGNORECASE),
    "lock": re.compile(r'lock[- ]?in\s+period[^.]*\d+\s*(?:year|month)', re.IGNORECASE),
    "risk": re.compile(r'(?:risk|riskometer)[^.]*\b(?:Low|Moderate|High|Very High)\b', re.IGNORECASE),
    "benchmark": re.compile(r'benchmark[^.]*\b[A-Z][^.,]+(?:Index|index)', re.IGNORECASE),
    "type": re.compile(r'(?:type|category|classified)[^.]*\b(?:Equity|Debt|Hybrid|Mid Cap|Large Cap|Small Cap)\b', re.IGNORECASE),
}


def _extract_from_chunks(query: str, chunks: List[Dict]) -> str:
    """Extract answer from chunks when LLM returns 'not found'."""
    query_lower = query.lower()
    
    # Find matching pattern based on query keywords
    for keyword, pattern in _FALLBACK_PATTERNS.items():
        if keyword in query_lower:
            # Search all chunks for matching sentence
            for chunk in chunks:
                text = chunk.get("text", "")
                match = pattern.search(text)
                if match:
                    # Return the matched sentence (clean it up)
                    sentence = match.group(0).strip()
                    # Ensure it's a complete sentence
                    if not sentence.endswith("."):
                        # Find the end of the sentence
                        end = text.find(".", match.end())
                        if end != -1:
                            sentence = text[match.start():end+1]
                    return sentence
    
    # Generic fallback: return first sentence of top chunk
    if chunks:
        text = chunks[0].get("text", "")
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if sentences:
            return sentences[0]
    
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
