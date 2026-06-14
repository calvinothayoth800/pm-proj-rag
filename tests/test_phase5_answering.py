import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.answering.prompts import build_prompt
from pm_rag.core.answering.generator import generate_answer
from pm_rag.core.answering.formatter import format_final_response
from pm_rag.core.compliance.validators import validate_answer

def test_build_prompt_empty_chunks():
    prompt = build_prompt("What is exit load?", [])
    assert "No relevant context found" in prompt

def test_build_prompt_with_chunks():
    chunks = [{"text": "The exit load is 1%."}]
    prompt = build_prompt("What is exit load?", chunks)
    assert "The exit load is 1%." in prompt

def test_formatter_truncates_sentences():
    raw = "Sentence one. Sentence two. Sentence three. Sentence four."
    formatted = format_final_response(raw, "https://groww.in/test", "2026-05-29")
    assert "Sentence four." not in formatted
    assert "Sentence one." in formatted

def test_formatter_appends_footer():
    raw = "Sentence one."
    formatted = format_final_response(raw, "https://groww.in/test", "2026-05-29")
    assert "Source: https://groww.in/test" in formatted
    assert "Last updated from sources: 2026-05-29" in formatted

def test_generator_simulator_returns_fallback_if_no_chunks():
    ans, url, date = generate_answer("query", [])
    assert "Information not found" in ans

def test_generator_simulator_extracts_from_chunk():
    chunks = [{
        "text": "The exit load is 1% for 1 year. Another sentence.",
        "metadata": {"source_url": "https://groww.in/test", "last_checked": "2026-05-29"}
    }]
    ans, url, date = generate_answer("exit load", chunks)
    assert "exit load" in ans
    assert url == "https://groww.in/test"
    assert date == "2026-05-29"

def test_integration_answering_and_compliance():
    chunks = [{
        "text": "The exit load is 1% for 1 year.",
        "metadata": {"source_url": "https://groww.in/test", "last_checked": "2026-05-29"}
    }]
    raw_ans, url, date = generate_answer("exit load", chunks)
    final_ans = format_final_response(raw_ans, url, date)
    
    # Should pass Phase 4 strict compliance validators
    valid, reason = validate_answer(final_ans)
    assert valid, f"Generated answer failed compliance validation: {reason}"
