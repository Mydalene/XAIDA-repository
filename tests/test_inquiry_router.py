# ============================================================
# XAIDA 5.3
# tests/test_inquiry_router.py
# ============================================================
import pytest

from assistant.session_manager import (
    create_audit_session,
)

from assistant.inquiry_router import (
    route_inquiry,
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
# WORKFLOW SUMMARY
# ============================================================

def test_executive_summary():

    result = route_inquiry(
        "give me an executive summary"
    )

    assert (
        result.inquiry
        == "workflow_summary"
    )


def test_audit_overview():

    result = route_inquiry(
        "audit overview"
    )

    assert (
        result.inquiry
        == "workflow_summary"
    )


def test_walkthrough():

    result = route_inquiry(
        "walk me through the audit"
    )

    assert (
        result.inquiry
        == "workflow_summary"
    )


# ============================================================
# WORKFLOW GUIDANCE
# ============================================================

def test_next_step():

    result = route_inquiry(
        "what should i do next"
    )

    assert (
        result.inquiry
        == "workflow_guidance"
    )


def test_workflow_status():

    result = route_inquiry(
        "workflow status"
    )

    assert (
        result.inquiry
        == "workflow_guidance"
    )


# ============================================================
# DATASET
# ============================================================

def test_dataset_schema():

    result = route_inquiry(
        "show dataset schema"
    )

    assert (
        result.inquiry
        == "dataset_inquiry"
    )


# ============================================================
# DATA PREPARATION
# ============================================================

def test_missing_values():

    result = route_inquiry(
        "show missing values"
    )

    assert (
        result.inquiry
        == "data_preparation_inquiry"
    )


def test_quality_score_is_not_a_supported_inquiry():

    result = route_inquiry(
        "show quality score"
    )

    assert result.inquiry == "general_inquiry"


# ============================================================
# DUPLICATE REVIEW
# ============================================================

def test_duplicate_groups():

    result = route_inquiry(
        "show duplicate groups"
    )

    assert (
        result.inquiry
        == "duplicate_review_inquiry"
    )


# ============================================================
# ANALYSIS
# ============================================================

def test_risk_scores():

    result = route_inquiry(
        "show risk scores"
    )

    assert (
        result.inquiry
        == "analysis_inquiry"
    )


def test_anomalies():

    result = route_inquiry(
        "show detected anomalies"
    )

    assert (
        result.inquiry
        == "analysis_inquiry"
    )


# ============================================================
# EXPLAINABILITY
# ============================================================

def test_why_flagged():

    result = route_inquiry(
        "why was this transaction flagged"
    )

    assert (
        result.inquiry
        == "explainability_inquiry"
    )


def test_risk_drivers():

    result = route_inquiry(
        "show risk drivers"
    )

    assert (
        result.inquiry
        == "explainability_inquiry"
    )


def test_shap():

    result = route_inquiry(
        "show shap explanation"
    )

    assert (
        result.inquiry
        == "explainability_inquiry"
    )


# ============================================================
# AUDIT REVIEW
# ============================================================

def test_false_positive():

    result = route_inquiry(
        "show false positives"
    )

    assert (
        result.inquiry
        == "audit_review_inquiry"
    )


# ============================================================
# FINDINGS
# ============================================================

def test_open_findings():

    result = route_inquiry(
        "show open findings"
    )

    assert (
        result.inquiry
        == "findings_inquiry"
    )


# ============================================================
# REPORTING
# ============================================================

def test_reporting():

    result = route_inquiry(
        "show audit report"
    )

    assert (
        result.inquiry
        == "reporting_inquiry"
    )


# ============================================================
# LINEAGE
# ============================================================

def test_dataset_lineage():

    result = route_inquiry(
        "show dataset lineage"
    )

    assert (
        result.inquiry
        == "lineage_inquiry"
    )


def test_version_history():

    result = route_inquiry(
        "show version history"
    )

    assert (
        result.inquiry
        == "lineage_inquiry"
    )


# ============================================================
# AUDIT TRAIL
# ============================================================

def test_audit_trail():

    result = route_inquiry(
        "show audit trail"
    )

    assert (
        result.inquiry
        == "audit_trail_inquiry"
    )


def test_audit_history():

    result = route_inquiry(
        "show audit history"
    )

    assert (
        result.inquiry
        == "audit_trail_inquiry"
    )


# ============================================================
# FALLBACK
# ============================================================

def test_general_inquiry():

    result = route_inquiry(
        "tell me something interesting"
    )

    assert (
        result.inquiry
        == "general_inquiry"
    )


def test_confidence_exists():

    result = route_inquiry(
        "executive summary"
    )

    assert (
        result.confidence > 0
    )
