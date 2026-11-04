# ============================================================
# CONTEXT VALIDATION TESTS
# ============================================================

import pandas as pd
from assistant.context.reporting_context import (
    build_reporting_context,
)
from exports.excel_export import create_analysis_workbook

from assistant.context.global_context import (
    build_global_context,
)

from assistant.context.audit_readiness_context import (
    build_audit_readiness_context,
)

from assistant.context.lineage_context import (
    build_lineage_context,
)

from assistant.context.traceability_context import (
    build_traceability_context,
)

from assistant.context.audit_trail_context import (
    build_trail_context,
)

from assistant.context.dataset_context import (
    build_dataset_context,
)

from assistant.context.analysis_context import (
    build_analysis_context,
)

from assistant.context.explainability_context import (
    build_explainability_context,
)

from assistant.context.audit_review_context import (
    build_audit_review_context,
)

from assistant.context.findings_context import (
    build_findings_context,
)

from assistant.context.context_builder import (
    build_context,
)

def validate_fields(
    context,
    required,
):

    for field in required:

        assert (
            field in context
        ), (
            f"Missing: {field}"
        )

def test_global_context(
    mock_session,
):

    context = (
        build_global_context(
            mock_session
        )
    )

    required = [
        "workflow_stage",
        "next_recommended_step",
    ]

    validate_fields(
        context,
        required,
    )
    assert "active_tab" not in context


def test_context_exposes_requested_help_and_evidence(
    mock_session,
):
    mock_session.initialization = {
        "initialized": True,
        "dataset_loaded": False,
        "initialization_complete": False,
    }
    context = build_context(mock_session)

    assert "active_tab" not in context
    assert "initialization_complete" in context
    assert context["dataset_loaded"] is False
    assert "dataset_upload_requirements" in context
    assert "platform_navigation_help" in context
    assert "sample_dataset_catalog" in context
    assert "feature_engineering_methodology" in context
    assert "removed_duplicate_records" in context
    assert "anomaly_dataset_version" in context
    assert "risk_score_histogram" in context
    assert "dataset_change_history" in context
    assert "explainability_dataset_version" in context
    assert "findings_dataset_version" in context

def test_audit_readiness_context(
    mock_session,
):

    context = (
        build_audit_readiness_context(
            mock_session
        )
    )

    required = [
        "audit_readiness_score",
        "audit_readiness_status",
        "audit_ready",
        "audit_readiness_breakdown",
    ]

    validate_fields(
        context,
        required,
    )

def test_lineage_context(
    mock_session,
):

    context = (
        build_lineage_context(
            mock_session
        )
    )

    required = [
        "dataset_versions",
        "dataset_version_history",
        "dataset_lineage_summary",
    ]

    validate_fields(
        context,
        required,
    )

def test_traceability_context(
    mock_session,
):

    context = (
        build_traceability_context(
            mock_session
        )
    )

    required = [
        "finding_traceability",
        "traceability_available",
    ]

    validate_fields(
        context,
        required,
    )

def test_dataset_context(
    mock_session,
):

    context = (
        build_dataset_context(
            mock_session
        )
    )

    required = [
        "dataset_name",
        "dataset_version",
        "rows",
        "columns",
        "column_names",
        "column_types",
    ]

    validate_fields(
        context,
        required,
    )

def test_audit_trail_context(
    mock_session,
):

    context = (
        build_trail_context(
            mock_session
        )
    )

    required = [
        "audit_entry_count",
        "audit_entries",
        "recent_audit_events",
        "audit_timeline",
    ]

    validate_fields(
        context,
        required,
    )

def test_analysis_context(
    mock_session,
):

    context = (
        build_analysis_context(
            mock_session,
            {},
        )
    )

    required = [
        "analysis_sections",
        "analysis_workflow_steps",
        "flag_rate",
        "threshold",
        "can_open_explainability",
    ]

    validate_fields(
        context,
        required,
    )

def test_explainability_context(
    mock_session,
):

    context = (
        build_explainability_context(
            mock_session,
            [],
        )
    )

    metadata={
        "workflow_stage": "analysis",
        "active_tab": "Analysis",
        "next_recommended_step": "Open Explainability",
    }

    required = [
        "top_feature_drivers",
        "narrative_count",
        "explained_record_count",
        "audit_review_available",
    ]

    validate_fields(
        context,
        required,
    )


def test_explainability_context_handles_saved_explanations_without_shap_details(
    mock_session,
):
    mock_session.explainability["explained_records"] = [
        {"Source Record": 1}
    ]
    mock_session.analysis["results"] = {
        "explanations": [{"Source Record": 1}]
    }

    context = build_explainability_context(mock_session, [])

    assert context["explained_record_count"] == 0
    assert context["shap_contribution_details"] == []


def test_audit_review_context(
    mock_session,
):

    context = (
        build_audit_review_context(
            mock_session
        )
    )

    required = [
        "audit_review_complete",
        "remaining_reviews",
        "can_generate_findings",
    ]

    validate_fields(
        context,
        required,
    )

def test_findings_context(
    mock_session,
):

    context = (
        build_findings_context(
            mock_session
        )
    )

    required = [
        "total_findings",
        "findings_available",
        "findings_sections",
        "findings_workflow_steps",
    ]

    for field in required:

        assert field in context

def test_reporting_context(
    mock_session,
):

    context = (
        build_reporting_context(
            mock_session
        )
    )

    required = [
        "report_generated",
        "report_sections",
        "reporting_workflow_steps",
        "anonymous_survey_status",
        "excel_report_includes_dataset_versions",
        "excel_report_dataset_version_sheets",
        "excel_report_download_available",
        "evidence_tables_downloadable",
        "evidence_table_download_format",
    ]

    for field in required:

        assert field in context
    assert "anonymous" in context["anonymous_survey_status"].lower()
    assert "not available yet" in context["anonymous_survey_status"].lower()


def test_reporting_context_documents_excel_versions_and_table_downloads(
    mock_session,
):
    mock_session.analysis["dataset_versions"] = {
        1: pd.DataFrame({"Amount": [10, 20]}),
        2: pd.DataFrame({"Amount": [20]}),
    }
    mock_session.analysis["dataset_version_metadata"] = {
        1: {"stage": "Dataset Upload"},
        2: {"stage": "Duplicate Review"},
    }
    mock_session.analysis["report_generated"] = True
    mock_session.reporting = {"excel_ready": True}

    context = build_reporting_context(mock_session)

    assert context["excel_report_includes_dataset_versions"] is True
    assert context["excel_report_dataset_version_sheets"] == [
        {
            "version": "V1",
            "sheet_name": "V1_Dataset_Upload",
            "records": 2,
            "columns": 1,
        },
        {
            "version": "V2",
            "sheet_name": "V2_Duplicate_Review",
            "records": 1,
            "columns": 1,
        },
    ]
    assert context["excel_report_download_available"] is True
    assert context["evidence_tables_downloadable"] is True
    assert context["evidence_table_download_format"] == "CSV"


def test_excel_report_contains_each_dataset_version_sheet(mock_session):
    mock_session.analysis["dataset_versions"] = {
        1: pd.DataFrame({"Amount": [10, 20]}),
        2: pd.DataFrame({"Amount": [20]}),
    }
    mock_session.analysis["dataset_version_metadata"] = {
        1: {"stage": "Dataset Upload"},
        2: {"stage": "Duplicate Review"},
    }

    workbook = create_analysis_workbook(mock_session)
    sheet_names = pd.ExcelFile(workbook).sheet_names

    assert "V1_Dataset_Upload" in sheet_names
    assert "V2_Duplicate_Review" in sheet_names


def validate_fields(
    context,
    required,
):

    for field in required:

        assert (
            field in context
        ), (
            f"Missing: {field}"
        )
