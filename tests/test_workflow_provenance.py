import pandas as pd

from assistant.action_router import ActionRouter
from assistant.session_manager import create_audit_session
from orchestration.workflow_engine import get_next_recommended_step


def test_findings_version_records_source_dataset_version():
    session = create_audit_session()
    session.analysis["dataset_version"] = 3
    session.analysis["dataset_versions"] = {}
    session.analysis["dataset_version_metadata"] = {}
    session.review["records"] = pd.DataFrame(
        {
            "Anomaly Flag": [True, False],
            "Auditor Assessment": [
                "Confirmed Anomaly",
                "False Positive",
            ],
            "Risk Score": [0.9, 0.2],
        }
    )

    result = ActionRouter().generate_findings(session)

    assert result["success"]
    assert session.findings["source_dataset_version"] == 3
    assert session.findings["findings_dataset_version"] == 4
    assert session.findings["findings_dataframe"][
        "Source Dataset Version"
    ].tolist() == [3]
    assert (
        session.analysis["dataset_version_metadata"][4]["dataset_type"]
        == "findings"
    )


def test_report_must_be_generated_before_audit_completion():
    session = create_audit_session()
    session.metadata["workflow_stage"] = "reporting"
    router = ActionRouter()

    result = router.complete_audit(session)

    assert result["success"] is False
    assert session.metadata["workflow_stage"] == "reporting"

    session.reporting["pdf_ready"] = True
    result = router.complete_audit(session)

    assert result["success"] is True
    assert session.metadata["workflow_stage"] == "audit_completion"
    assert session.metadata["status"] == "completed"


def test_next_recommended_step_tracks_duplicate_and_analysis_completion():
    session = create_audit_session()
    session.metadata["workflow_stage"] = "duplicate_review"
    session.duplicates["duplicate_count"] = 3

    assert get_next_recommended_step(session) == "Complete Duplicate Review"

    session.duplicates["strategy"] = "retain_first"
    session.duplicates["duplicate_review_complete"] = True
    assert get_next_recommended_step(session) == "Proceed To Analysis"

    session.metadata["workflow_stage"] = "analysis"
    assert get_next_recommended_step(session) == "Run Analysis"

    session.analysis["analysis_complete"] = True
    assert get_next_recommended_step(session) == "Open Explainability"


def test_audit_review_recommends_review_then_save_then_findings():
    session = create_audit_session()
    session.metadata["workflow_stage"] = "audit_review"
    session.review["records"] = pd.DataFrame(
        {
            "Anomaly Flag": [True, False],
            "Auditor Assessment": [None, None],
        }
    )

    assert get_next_recommended_step(session) == "Review flagged records"

    session.review["records"].loc[0, "Auditor Assessment"] = (
        "Confirmed Anomaly"
    )
    assert get_next_recommended_step(session) == "Save Review Decisions"

    session.review["audit_review_complete"] = True
    assert get_next_recommended_step(session) == "Proceed To Findings"
