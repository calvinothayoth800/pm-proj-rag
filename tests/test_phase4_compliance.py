import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_rag.core.compliance.classifier import classify_query_intent, detect_sensitive_data, is_allowed_query
from pm_rag.core.compliance.validators import validate_answer, validate_sentence_count, validate_source_link, validate_footer_format


def test_classify_expense_ratio_query():
    intent = classify_query_intent("What is the expense ratio?")
    assert intent == "expense_ratio", f"expected expense_ratio, got {intent}"


def test_classify_exit_load_query():
    intent = classify_query_intent("What is the exit load?")
    assert intent == "exit_load", f"expected exit_load, got {intent}"


def test_classify_lock_in_query():
    intent = classify_query_intent("What is the lock-in period for ELSS?")
    assert intent == "lock_in_period", f"expected lock_in_period, got {intent}"


def test_classify_refused_advisory_query():
    intent = classify_query_intent("Should I invest in this fund?")
    assert intent == "investment_advice", f"expected investment_advice, got {intent}"


def test_classify_refused_comparison_query():
    intent = classify_query_intent("Compare these funds?")
    assert intent == "comparison", f"expected comparison, got {intent}"


def test_classify_refused_recommendation_query():
    intent = classify_query_intent("Recommend me a mutual fund.")
    assert intent == "investment_advice", f"expected investment_advice, got {intent}"


def test_detect_no_sensitive_data_in_factual_query():
    has_sensitive, pattern = detect_sensitive_data("What is the expense ratio?")
    assert not has_sensitive, f"should not detect sensitive data, but got: {pattern}"


def test_detect_pan_request():
    has_sensitive, pattern = detect_sensitive_data("What is my PAN?")
    assert has_sensitive, f"should detect PAN, got: {pattern}"
    assert "pan" in pattern.lower(), f"pattern should mention PAN, got: {pattern}"


def test_detect_aadhaar_request():
    has_sensitive, pattern = detect_sensitive_data("Can you provide my Aadhaar?")
    assert has_sensitive, f"should detect Aadhaar"


def test_detect_otp_request():
    has_sensitive, pattern = detect_sensitive_data("What is my OTP?")
    assert has_sensitive, f"should detect OTP"


def test_is_allowed_query_for_factual():
    allowed, reason = is_allowed_query("What is the expense ratio?")
    assert allowed, f"factual query should be allowed, reason: {reason}"


def test_is_allowed_query_rejects_advisory():
    allowed, reason = is_allowed_query("Should I invest in HDFC Focused?")
    assert not allowed, f"advisory query should be rejected"
    assert "not allowed" in reason.lower(), f"reason should mention not allowed: {reason}"


def test_is_allowed_query_rejects_sensitive():
    allowed, reason = is_allowed_query("What is my account number?")
    assert not allowed, f"sensitive data query should be rejected"
    assert "sensitive" in reason.lower(), f"reason should mention sensitive: {reason}"


def test_validate_sentence_count_valid():
    answer = "Expense ratio is seventy-five basis points. It is a direct fund. Details available on Groww link"
    valid, reason = validate_sentence_count(answer)
    assert valid, f"3-sentence answer should be valid: {reason}"


def test_validate_sentence_count_exceeds_limit():
    answer = "The expense ratio is 0.75%. It is a direct fund. You can check Groww. There's more info. And more."
    valid, reason = validate_sentence_count(answer)
    assert not valid, f"5-sentence answer should be invalid, but was valid: {reason}"


def test_validate_source_link_single_required():
    answer = "Details: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    valid, reason = validate_source_link(answer)
    assert valid, f"single source link should be valid: {reason}"


def test_validate_source_link_missing():
    answer = "The expense ratio is 0.75%."
    valid, reason = validate_source_link(answer)
    assert not valid, f"missing source link should be invalid"


def test_validate_source_link_multiple_forbidden():
    answer = "Details: https://groww.in/link1 and https://groww.in/link2"
    valid, reason = validate_source_link(answer)
    assert not valid, f"multiple source links should be invalid"


def test_validate_footer_format_valid():
    answer = "Details here. Last updated from sources: 2026-05-29"
    valid, reason = validate_footer_format(answer)
    assert valid, f"valid footer should pass: {reason}"


def test_validate_footer_format_missing():
    answer = "Details here."
    valid, reason = validate_footer_format(answer)
    assert not valid, f"missing footer should fail"


def test_validate_footer_format_wrong_date():
    answer = "Details. Last updated from sources: 05-29-2026"
    valid, reason = validate_footer_format(answer)
    assert not valid, f"wrong date format should fail"


def test_validate_answer_full_compliance():
    answer = (
        "The expense ratio is low percentage-wise. "
        "It is a direct plan option. "
        "See https://example-groww-link/fund for details. "
        "Last updated from sources: 2026-05-29"
    )
    valid, reason = validate_answer(answer)
    assert valid, f"compliant answer should be valid: {reason}"


def test_validate_answer_exceeds_sentences():
    answer = (
        "The expense ratio is 0.75%. "
        "It is a direct plan. "
        "It is a growth option. "
        "It is a suitable fund. "
        "See https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth "
        "Last updated from sources: 2026-05-29"
    )
    valid, reason = validate_answer(answer)
    assert not valid, f"answer exceeding 3 sentences should be invalid"


def test_validate_answer_no_source_link():
    answer = (
        "The expense ratio is 0.75%. "
        "It is a direct plan. "
        "Check the official website. "
        "Last updated from sources: 2026-05-29"
    )
    valid, reason = validate_answer(answer)
    assert not valid, f"answer without source link should be invalid"


def test_validate_answer_no_footer():
    answer = (
        "The expense ratio is 0.75%. "
        "It is a direct plan. "
        "See https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
    )
    valid, reason = validate_answer(answer)
    assert not valid, f"answer without footer should be invalid"


def test_compliance_integration_factual_allowed():
    query = "What is the lock-in period for ELSS?"
    allowed, reason = is_allowed_query(query)
    assert allowed, f"factual query should be allowed: {reason}"
    
    answer = (
        "ELSS funds have a three-year lock-in mandate. "
        "This is required by SEBI regulations. "
        "See https://example-groww-elss/details for more info. "
        "Last updated from sources: 2026-05-29"
    )
    valid, reason = validate_answer(answer)
    assert valid, f"compliant answer should pass validation: {reason}"


def test_compliance_integration_advisory_rejected():
    query = "Should I invest in HDFC Equity Fund?"
    allowed, reason = is_allowed_query(query)
    assert not allowed, f"advisory query should be rejected: {reason}"


def test_compliance_integration_sensitive_rejected():
    query = "Can you verify my Aadhaar number?"
    allowed, reason = is_allowed_query(query)
    assert not allowed, f"sensitive data query should be rejected"
