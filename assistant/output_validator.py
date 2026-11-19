# ============================================================
# XAIDA 5.0
# assistant/output_validator.py
# ============================================================

import re


RESPONSE_LANGUAGE_INSTRUCTION = (
    'Never use the standalone words "business" or "context" in any '
    "user-facing response. Rephrase the sentence to avoid them."
)

FORBIDDEN_PHRASES = [
    "i think",
    "i believe",
]

FORBIDDEN_TERMS = [
    "business",
    "context",
]

def validate_response(response):

    if not response:
        return (
            False,
            "Information unavailable in the current audit session.",
        )

    lower = response.lower()

    for phrase in FORBIDDEN_PHRASES:
        if phrase in lower:
            return (
                False,
                (
                    "The generated response contained "
                    "unsupported personal opinion and was suppressed."
                ),
            )

    for term in FORBIDDEN_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lower):
            return (
                False,
                "The generated response contained restricted wording "
                "and was suppressed.",
            )

    return (
        True,
        response,
    )