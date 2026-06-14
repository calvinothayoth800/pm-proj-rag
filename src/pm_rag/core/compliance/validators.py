import re
from typing import Tuple

from pm_rag.core.compliance.policies import ANSWER_CONSTRAINTS


def validate_sentence_count(answer: str) -> Tuple[bool, str]:
    """Check that answer is at most 3 sentences (excluding footer)."""
    # Remove footer before counting sentences
    answer_without_footer = re.sub(r'Last updated from sources: \d{4}-\d{2}-\d{2}', '', answer)
    protected = re.sub(r'https?://[^\s)]+', 'URL', answer_without_footer)
    protected = re.sub(r'(?<=\d)\.(?=\d)', 'DECIMAL', protected)
    sentences = [s.strip() for s in re.split(r'[.!?]+', protected) if s.strip()]
    if len(sentences) > ANSWER_CONSTRAINTS["max_sentences"]:
        return False, f"answer has {len(sentences)} sentences; max is {ANSWER_CONSTRAINTS['max_sentences']}"
    return True, ""


def validate_source_link(answer: str) -> Tuple[bool, str]:
    """Check that answer contains exactly 1 source link."""
    links = re.findall(r'https?://[^\s)]+', answer)
    if len(links) != 1:
        return False, f"answer has {len(links)} links; exactly 1 required"
    return True, ""


def validate_footer_format(answer: str) -> Tuple[bool, str]:
    """Check that answer ends with required footer."""
    footer_pattern = r"Last updated from sources: \d{4}-\d{2}-\d{2}"
    if not re.search(footer_pattern, answer):
        return False, "missing or malformed footer (expected: Last updated from sources: YYYY-MM-DD)"
    return True, ""


def validate_no_advisory_content(answer: str) -> Tuple[bool, str]:
    """Check that answer does not contain advisory/recommendation keywords."""
    advisory_keywords = [
        "should", "you should", "i recommend", "consider", "suggest", "better",
        "best practice", "best fund", "will make money", "will earn", "likely return"
    ]
    answer_lower = answer.lower()
    for keyword in advisory_keywords:
        if keyword in answer_lower:
            return False, f"answer contains advisory keyword: '{keyword}'"
    return True, ""


def validate_answer(answer: str, source_url: str = None, last_checked: str = None) -> Tuple[bool, str]:
    """
    Validate that answer meets all compliance constraints.
    Returns (is_valid, reason).
    
    Args:
        answer: full answer text to validate
        source_url: optional source URL to verify
        last_checked: optional last-checked date to verify in footer
    
    Returns:
        (is_valid, error_message)
    """
    # Check sentence count
    valid, reason = validate_sentence_count(answer)
    if not valid:
        return False, reason
    
    # Check source link presence
    if ANSWER_CONSTRAINTS["required_source_link"]:
        valid, reason = validate_source_link(answer)
        if not valid:
            return False, reason
    
    # Check footer format
    if ANSWER_CONSTRAINTS["required_footer"]:
        valid, reason = validate_footer_format(answer)
        if not valid:
            return False, reason
    
    # Check no advisory content
    valid, reason = validate_no_advisory_content(answer)
    if not valid:
        return False, reason
    
    return True, ""
