# ============================================================
# XAIDA CONTEXT ROUTER TESTS
# ============================================================

import pytest

from assistant.session_manager import (
    create_audit_session,
)

# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def empty_session():

    session = create_audit_session()

    session.metadata[
        "workflow_stage"
    ] = "analysis"

    return session

# ============================================================
# tests/test_context_router.py
# ============================================================

from assistant.context_router import (
    classify_question,
)

# ============================================================
# DATASET
# ============================================================

def test_dataset_schema():

    category = classify_question(
        "show dataset schema"
    )

    assert category == "dataset"


def test_dataset_columns():

    category = classify_question(
        "what columns are available"
    )

    assert category == "dataset"


# ============================================================
# DATA PREPARATION
# ============================================================

def test_missing_values():

    category = classify_question(
        "show missing values"
    )

    assert category == "data_preparation"


def test_quality_score_is_not_a_supported_inquiry():

    category = classify_question(
        "explain quality score"
    )

    assert category == "general"


# ============================================================
# DUPLICATE REVIEW
# ============================================================

def test_duplicate_groups():

    category = classify_question(
        "show duplicate groups"
    )

    assert category == "duplicate_review"


def test_duplicate_strategy():

    category = classify_question(
        "which duplicate strategy was used"
    )

    assert category == "duplicate_review"


# ============================================================
# ANALYSIS
# ============================================================

def test_risk_scores():

    category = classify_question(
        "show risk scores"
    )

    assert category == "analysis"


def test_anomalies():

    category = classify_question(
        "why was this transaction flagged"
    )

    assert category == "explainability"


# ============================================================
# EXPLAINABILITY
# ============================================================

def test_shap():

    category = classify_question(
        "show shap explanation"
    )

    assert category == "explainability"


# ============================================================
# AUDIT REVIEW
# ============================================================

def test_false_positives():

    category = classify_question(
        "show false positives"
    )

    assert category == "audit_review"


# ============================================================
# FINDINGS
# ============================================================

def test_open_findings():

    category = classify_question(
        "show open findings"
    )

    assert category == "findings"


# ============================================================
# REPORTING
# ============================================================

def test_reporting():

    category = classify_question(
        "generate report"
    )

    assert category == "reporting"


# ============================================================
# LINEAGE
# ============================================================

def test_lineage():

    category = classify_question(
        "show dataset lineage"
    )

    assert category == "lineage"


# ============================================================
# AUDIT TRAIL
# ============================================================

def test_audit_trail():

    category = classify_question(
        "show audit history"
    )

    assert category == "audit_trail"


# ============================================================
# WORKFLOW
# ============================================================

def test_workflow_status():

    category = classify_question(
        "what is the current workflow stage"
    )

    assert category == "workflow"


def test_audit_summary():

    category = classify_question(
        "give me an executive summary"
    )

    assert category == "workflow"


def test_audit_retrospective():

    category = classify_question(
        "walk me through the audit"
    )

    assert category == "workflow"