# ============================================================
# XAIDA 5.0
# assistant/output_validator.py
# ============================================================

FORBIDDEN_PHRASES = [
    "i think",
    "i believe",
]


FORBIDDEN_PHRASES = [
    "i think",
    "i believe",
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

    return (
        True,
        response,
    )