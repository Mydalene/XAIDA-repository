# ============================================================
# XAIDA Smoke Test
# ============================================================

from assistant.context_router import (
    classify_question,
)


def test_context_router_analysis():

    result = classify_question(
        "What anomaly detection algorithms were used?"
    )

    assert result == "analysis"


def test_context_router_duplicates():

    result = classify_question(
        "How does XAIDA detect duplicates?"
    )

    assert result == "duplicate_review"


def test_context_router_missing_values():

    result = classify_question(
        "What imputation rules were used?"
    )

    assert result == "data_preparation"