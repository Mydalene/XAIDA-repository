import threading

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


def test_confirm_all_flagged_records_waits_for_running_analysis():
    session = create_audit_session()
    session.analysis["analysis_complete"] = True
    session.analysis["analysis_running"] = True
    session.review["records"] = pd.DataFrame(
        {
            "Anomaly Flag": [True],
            "Auditor Assessment": [None],
        }
    )

    result = ActionRouter().confirm_all_flagged_records(session)

    assert result["success"] is False
    assert "still running" in result["message"]
    assert pd.isna(
        session.review["records"].loc[0, "Auditor Assessment"]
    )
    assert not session.review.get("bulk_confirmation_complete", False)


def test_confirm_all_flagged_records_handles_missing_analysis_flags():
    session = create_audit_session()
    session.analysis["analysis_complete"] = True
    session.review["records"] = pd.DataFrame(
        {"Auditor Assessment": [None]}
    )

    result = ActionRouter().confirm_all_flagged_records(session)

    assert result["success"] is False
    assert "does not contain analysis flags" in result["message"]


def test_confirm_all_flagged_records_is_idempotent_and_ignores_null_flags():
    session = create_audit_session()
    session.analysis["analysis_complete"] = True
    session.review["records"] = pd.DataFrame(
        {
            "Anomaly Flag": [True, False, None],
            "Auditor Assessment": [None, None, None],
        }
    )

    router = ActionRouter()
    first_result = router.confirm_all_flagged_records(session)
    audit_log_length = len(session.audit_log)
    second_result = router.confirm_all_flagged_records(session)

    assert first_result["success"] is True
    assert second_result["success"] is True
    assert session.review["records"]["Auditor Assessment"].tolist() == [
        "Confirmed Anomaly",
        None,
        None,
    ]
    assert session.review["bulk_confirmation_complete"] is True
    assert len(session.audit_log) == audit_log_length


def test_duplicate_flagged_record_confirmation_is_rejected():
    session = create_audit_session()
    router = ActionRouter()
    action_started = threading.Event()
    release_action = threading.Event()

    def wait_for_action(_session):
        action_started.set()
        assert release_action.wait(timeout=5)
        return {"success": True, "message": "Action completed."}

    router.confirm_all_flagged_records = wait_for_action

    action_thread = threading.Thread(
        target=lambda: router.execute(
            "confirm_all_flagged_records",
            session,
        ),
    )
    action_thread.start()
    try:
        assert action_started.wait(timeout=5)
        duplicate_result = router.execute(
            "confirm_all_flagged_records",
            session,
        )
    finally:
        release_action.set()
        action_thread.join(timeout=5)

    assert not action_thread.is_alive()
    assert duplicate_result["success"] is False
    assert "already running" in duplicate_result["message"]
    assert router.execute(
        "confirm_all_flagged_records",
        session,
    )["success"] is True


def test_action_router_rejects_other_workflow_actions_during_analysis():
    session = create_audit_session()
    session.analysis["analysis_running"] = True

    result = ActionRouter().execute("manual_review", session)

    assert result["success"] is False
    assert "still running" in result["message"]
    assert not session.review.get("manual_review_mode", False)
