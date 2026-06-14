def format_final_response(raw_answer: str, source_url: str, last_checked: str) -> str:
    """
    Formats the raw answer to enforce the contract:
    - Truncates to max 2 sentences if needed.
    - Appends exactly one source link.
    - Appends the Last updated footer.
    """
    if not raw_answer.strip():
        raw_answer = "Information not found in the fixed Groww corpus."
        
    # Split into sentences very simply for truncation
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', raw_answer.strip()) if s.strip()]
    if len(sentences) > 2:
        sentences = sentences[:2]
    
    truncated_answer = " ".join(sentences)
    
    parts = [truncated_answer]
    if source_url:
        parts.append(f"Source: {source_url}")
    if last_checked:
        parts.append(f"Last updated from sources: {last_checked}")
        
    return " ".join(parts)
