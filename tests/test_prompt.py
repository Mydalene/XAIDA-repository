# ============================================================
# XAIDA PROMPT VALIDATION TESTS
# ============================================================

import pytest

from assistant.session_manager import (
    create_audit_session,
)

from assistant.prompts.stage_prompts import (

    get_dataset_prompt,
    get_data_preparation_prompt,
    get_duplicate_review_prompt,
    get_analysis_prompt,
    get_explainability_prompt,
    get_audit_review_prompt,
    get_reporting_prompt,
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
# HELPER
# ============================================================

def validate_prompt_contains(
    prompt,
    required,
):

    for term in required:

        assert (
            term in prompt
        ), (
            f"Missing prompt term: {term}"
        )

def test_dataset_prompt():

    context = {
        "dataset_name": "Test Dataset",
        "rows": 100,
        "columns": 5,
        "column_names": [
            "A",
            "B",
        ],
    }

    prompt = (
        get_dataset_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "Dataset Name",
            "Rows",
            "Columns",
            "Dataset Metadata",
        ],
    )

def test_data_preparation_prompt():

    context = {
        "audit_readiness_score": 98,
        "audit_ready": True,
    }

    prompt = (
        get_data_preparation_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "Data Preparation",
            "Audit Readiness",
            "next_recommended_step",
        ],
    )

def test_duplicate_review_prompt():

    context = {
        "duplicate_count": 10,
        "duplicate_groups": 3,
        "duplicate_review_complete": False,
    }

    prompt = (
        get_duplicate_review_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "Duplicate",
            "Explain the workflow recommendation",
            "next_recommended_step",
        ],
    )


def test_analysis_prompt(
    mock_session,
):

    context = {
        "threshold": 0.8,
        "flag_rate": 4.5,
        "analysis_sections": [],
        "analysis_workflow_steps": [],
        "audit_readiness_score": 90,
        "audit_readiness_status":
            "Audit Ready",
    }

    prompt = (
        get_analysis_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "Threshold",
            "Flag Rate",
            "Audit Readiness",
            "Next Recommended Step",
        ],
    )

def test_explainability_prompt():

    context = {
        "top_feature_drivers": [],
        "explainability_sections": [],
        "explainability_workflow_steps": [],
    }

    prompt = (
        get_explainability_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "SHAP",
            "Explainability",
            "Top Feature Drivers",
            "WORKFLOW RECOMMENDATION RULES",
        ],
    )

def test_audit_review_prompt():

    context = {
        "remaining_reviews": 0,
        "can_generate_findings": True,
        "audit_review_complete": True,
    }

    prompt = (
        get_audit_review_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "Review Complete",
            "Remaining Reviews",
            "Audit Review Complete",
            "Proceed To Findings",
        ],
    )

def test_reporting_prompt():

    context = {
        "report_generated": True,
        "report_sections": [],
        "reporting_workflow_steps": [],
        "excel_report_includes_dataset_versions": True,
        "excel_report_dataset_version_sheets": ["V1_Dataset"],
        "excel_report_download_available": True,
        "evidence_tables_downloadable": True,
        "evidence_table_download_format": "CSV",
    }

    prompt = (
        get_reporting_prompt(
            context
        )
    )

    validate_prompt_contains(
        prompt,
        [
            "Report Generated",
            "Audit Readiness Score",
            "REPORTING INTEGRITY RULES",
            "Excel Report Includes Dataset Versions",
            "V1_Dataset",
            "Evidence Panel Tables Downloadable",
            "CSV",
            "PDF Export Available",
        ],
    )

def test_workflow_rule_present():

    prompt = get_analysis_prompt(
        {}
    )

    assert (
        "Next Recommended Step:"
        in prompt
    )

def test_workflow_recommendation_rules_present():

    prompts = [

        get_data_preparation_prompt({}),
        get_duplicate_review_prompt({}),
        get_analysis_prompt({}),
        get_explainability_prompt({}),
    ]

    for prompt in prompts:

        assert (
            "next_recommended_step" in prompt.lower()
            or "next recommended step" in prompt.lower()
        )

        assert "navigation rules" not in prompt.lower()