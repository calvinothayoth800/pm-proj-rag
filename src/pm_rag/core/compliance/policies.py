# Central policy definitions for query classification and answer validation.

ALLOWED_QUERY_INTENTS = {
    "expense_ratio",
    "exit_load",
    "minimum_sip",
    "minimum_investment",
    "lock_in_period",
    "riskometer",
    "benchmark",
    "document_download",
    "tax_statement",
    "factual_question",
}

REFUSED_QUERY_INTENTS = {
    "investment_advice",
    "recommendation",
    "comparison",
    "ranking",
    "performance_calculation",
    "return_projection",
    "should_i_invest",
    "which_fund_better",
}

SENSITIVE_DATA_PATTERNS = [
    "pan",
    "aadhaar",
    "account number",
    "account balance",
    "my account",
    "otp",
    "password",
    "email",
    "phone number",
    "mobile",
]

ANSWER_CONSTRAINTS = {
    "max_sentences": 3,
    "required_source_link": True,
    "required_footer": True,
    "footer_format": "Last updated from sources: {date}",
}

REFUSAL_MESSAGE_TEMPLATE = """
I can't help with that. This is a facts-only assistant focused on objective mutual fund information. 
For investment advice, please consult a financial advisor or visit official resources.
"""

INSUFFICIENCY_MESSAGE_TEMPLATE = """
I didn't find that information in the fixed Groww corpus. Please check the official Groww pages or contact support.
"""
