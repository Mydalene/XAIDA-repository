import pandas as pd

from assistant.context.context_builder import build_context
from assistant.context.explainability_context import build_explainability_context
from assistant.context_router import classify_question
from assistant.prompts.prompt_builder import build_system_messages
from assistant.prompts.system_prompt import get_system_prompt
from assistant.session_manager import create_audit_session
from audit.change_tracker import log_dataset_change
from dataset.duplicate_resolution import remove_duplicate_copies


def test_requested_audit_details_are_available_to_xaida():
    session = create_audit_session()
    session.analysis["dataset_version_metadata"] = {
        2: {
            "stage": "Analysis",
            "action": "Anomaly Dataset Generated",
            "dataset_type": "anomaly",
        },
        3: {
            "stage": "Explainability",
            "action": "Explainability Dataset Generated",
            "dataset_type": "explainability",
        },
    }
    session.analysis["explainability_version"] = 3
    session.analysis["results"] = {
        "analysis_dataframe": pd.DataFrame(
            {
                "Risk Score": [0.1, 0.4, 0.7, 0.9],
                "Anomaly Flag": [False, False, True, True],
            }
        ),
        "threshold": 0.6,
    }
    session.duplicates["removed_duplicate_records"] = pd.DataFrame(
        {"transaction_id": [17], "amount": [500]}
    )
    session.duplicates["strategy"] = "retain_first"
    session.findings.update(
        {
            "source_dataset_version": 3,
            "findings_dataset_version": 4,
        }
    )
    log_dataset_change(
        session,
        stage="Data Preparation",
        action="Missing-value imputation",
        details="Applied a recorded imputation rule.",
        version=1,
    )

    context = build_context(session)

    assert context["dataset_upload_requirements"]["accepted_formats"] == [
        ".csv",
        ".xlsx",
    ]
    assert context["sample_dataset_catalog"] == [
        "Accounts Payable",
        "Accounts Receivable",
        "Budget Forecast",
        "Expense Claims",
        "General Ledger",
    ]
    assert "Lineage" in context["platform_navigation_help"]["evidence_tabs"]
    assert context["feature_engineering_methodology"]
    assert context["anomaly_dataset_version"] == 2
    assert context["explainability_dataset_version"] == 3
    assert context["findings_dataset_version"] == 4
    assert context["dataset_change_history"][0]["action"] == (
        "Missing-value imputation"
    )
    assert context["removed_duplicate_records"] == {
        "available": True,
        "record_count": 1,
        "columns": ["transaction_id", "amount"],
    }
    histogram = context["risk_score_histogram"]
    assert histogram["normal_records"] == 2
    assert histogram["anomaly_records"] == 2
    assert histogram["bin_count"] == 30
    prompt = get_system_prompt(context)
    assert ".csv" in prompt and ".xlsx" in prompt
    assert "Accounts Payable" in prompt
    assert "dataset_change_history" not in prompt
    assert "record-level samples" in prompt
    evidence_snapshot = build_system_messages(context)[-1]["content"]
    assert "Complete audit evidence snapshot" in evidence_snapshot
    assert '"risk_score_histogram"' in evidence_snapshot
    assert '"removed_duplicate_record_sample"' in evidence_snapshot


def test_requested_questions_route_to_relevant_evidence():
    assert classify_question("How do I start a new audit?") == "initialization"
    assert classify_question("What files can I upload?") == "dataset"
    assert classify_question("Which sample datasets are available?") == "dataset"
    assert classify_question("Where is the dataset lineage tab?") == "lineage"
    assert classify_question("Show the risk score histogram") == "analysis"
    assert classify_question("What is the anomaly dataset version?") == "lineage"
    assert classify_question("What is the explainability dataset version?") == (
        "lineage"
    )
    assert classify_question("What is the findings dataset version?") == "lineage"


def test_full_evidence_snapshot_serializes_bounded_dataframe_records():
    messages = build_system_messages(
        {
            "top_features": pd.DataFrame(
                {"feature": ["amount"], "importance": [0.8]}
            )
        }
    )

    assert '"records": [{"feature": "amount", "importance": 0.8}]' in (
        messages[2]["content"]
    )


def test_missing_record_identifiers_are_included_in_evidence():
    session = create_audit_session()
    session.dataset["dataframe"] = pd.DataFrame(
        {
            "Transaction ID": [101, 102, 103],
            "Amount": [10.0, None, None],
        },
        index=[5, 6, 7],
    )

    context = build_context(
        session,
        user_message="List all affected record IDs.",
    )

    amount = next(
        item
        for item in context["missing_record_identifiers"]
        if item["column"] == "Amount"
    )
    assert amount["missing_record_count"] == 2
    assert [item["record_id"] for item in amount["record_identifiers"]] == [
        102,
        103,
    ]


def test_duplicate_removal_schedule_maps_removed_to_retained_source_rows():
    session = create_audit_session()
    session.dataset["dataframe"] = pd.DataFrame(
        {"Transaction ID": [501, 501, 502], "Amount": [20, 20, 30]},
        index=[10, 11, 12],
    )

    remove_duplicate_copies(session)

    schedule = session.duplicates["duplicate_removal_schedule"]
    assert len(schedule) == 1
    assert schedule[0]["retained_source_row_position"] == 1
    assert schedule[0]["removed_source_row_position"] == 2
    assert schedule[0]["retained_record"] == schedule[0]["removed_record"]
    context = build_context(session)
    assert context["duplicate_removal_schedule"] == schedule


def test_explainability_does_not_repeat_open_audit_review_in_audit_review_stage():
    session = create_audit_session()
    session.metadata["workflow_stage"] = "audit_review"

    context = build_explainability_context(session, top_features=None)

    assert "Open Audit Review" not in context["explainability_workflow_steps"]
    assert context["explainability_workflow_steps"][-1] == (
        "Review flagged records"
    )


def test_report_context_exposes_frozen_findings_dataset_version():
    session = create_audit_session()
    session.findings.update(
        {
            "report_dataset_version": 7,
            "source_dataset_version": 5,
            "findings_locked": True,
        }
    )
    session.analysis["dataset_versions"] = {
        7: pd.DataFrame({"Finding ID": ["F-001"]})
    }

    context = build_context(session)

    assert context["report_dataset_version"] == 7
    assert context["report_source_dataset_version"] == 5
    assert context["findings_locked"] is True
    assert context["dataset_versions_downloadable"] is True
    assert context["dataset_version_download_format"] == "CSV"
