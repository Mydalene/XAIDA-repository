from pathlib import Path
import os
import sqlite3

import pandas as pd
from google.auth.exceptions import DefaultCredentialsError
from streamlit.testing.v1 import AppTest

from assistant.conversation_manager import (
    add_assistant_message,
    add_user_message,
)
from assistant.copilot import XaidaCopilot
from orchestration.workflow_engine import get_next_recommended_step

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _start_app():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)
    app.checkbox(key="xaida_security_statement_ack").check().run(timeout=30)
    return app.button(key="xaida_start_session").click().run(timeout=30)


def test_security_statement_must_be_acknowledged_before_audit_session_starts():
    app = AppTest.from_file(str(APP_PATH)).run(timeout=30)

    assert not app.exception
    assert any(
        "XAIDA Security and Confidentiality Statement" in item.value
        for item in app.title
    )
    statement = " ".join(
        "\n".join(item.value for item in app.markdown).split()
    )
    assert "Evaluation metrics are stored separately from audit evidence" in statement
    assert "Vertex AI assistant" in statement
    assert "audit_session" not in app.session_state

    app = app.checkbox(key="xaida_security_statement_ack").check().run(
        timeout=30
    )
    assert "audit_session" not in app.session_state

    app = app.button(key="xaida_start_session").click().run(timeout=30)
    assert not app.exception
    assert "audit_session" in app.session_state


def test_assistant_dialog_remains_open_after_question(monkeypatch):
    def fake_chat(self, session, prompt):
        add_user_message(session, prompt)
        add_assistant_message(session, "Mock assistant response")
        session.conversation[-1]["interaction_id"] = "test-interaction"

    monkeypatch.setattr(XaidaCopilot, "chat", fake_chat)
    app = _start_app()
    assert any(
        "sends relevant audit evidence to the" in item.value
        and "organization has approved that service" in item.value
        for item in app.warning
    )
    assert (
        app.session_state["audit_session"].metadata["workflow_stage"]
        == "initialization"
    )

    assistant_button = next(
        button
        for button in app.button
        if button.label == "XAIDA Vertex AI Assistant"
    )
    app = assistant_button.click().run(timeout=30)
    assert len(app.chat_input) == 1
    assert (
        app.chat_input[0].placeholder
        == "Ask the Vertex AI assistant..."
    )
    assert any(
        "Welcome to XAIDA Vertex AI Assistant." in item.value
        for item in app.markdown
    )

    app = app.chat_input[0].set_value(
        "How many records are loaded?"
    ).run(timeout=30)

    assert not app.exception
    assert len(app.chat_input) == 1
    assert "Mock assistant response" in [
        item.value for item in app.markdown
    ]
    assert any(
        "grounded in the audit evidence" in radio.label.lower()
        for radio in app.radio
    )


def test_chatbot_shows_actionable_message_when_vertex_transfer_is_not_approved(
    monkeypatch,
):
    def blocked_chat(self, session, prompt):
        raise RuntimeError(
            "XAIDA Vertex AI Assistant data transfer is disabled. Set "
            "XAIDA_VERTEX_AI_APPROVED=true only after the organization "
            "approves the configured Vertex AI project, region, and data "
            "handling controls."
        )

    monkeypatch.setattr(XaidaCopilot, "chat", blocked_chat)
    app = _start_app()
    assistant_button = next(
        button
        for button in app.button
        if button.label == "XAIDA Vertex AI Assistant"
    )
    app = assistant_button.click().run(timeout=30)
    app = app.chat_input[0].set_value(
        "How many records are loaded?"
    ).run(timeout=30)

    assert not app.exception
    error = " ".join(item.value for item in app.error)
    assert "data transfer is disabled" in error
    assert "only after the organization approves" in error


def test_chatbot_shows_local_adc_setup_when_vertex_credentials_are_missing(
    monkeypatch,
):
    def missing_credentials(self, session, prompt):
        raise DefaultCredentialsError("Credentials are not configured.")

    monkeypatch.setattr(XaidaCopilot, "chat", missing_credentials)
    app = _start_app()
    assistant_button = next(
        button
        for button in app.button
        if button.label == "XAIDA Vertex AI Assistant"
    )
    app = assistant_button.click().run(timeout=30)
    app = app.chat_input[0].set_value(
        "Check the AI setup"
    ).run(timeout=30)

    assert not app.exception
    error = " ".join(item.value for item in app.error)
    assert "Google Cloud credentials are not configured" in error
    assert "gcloud auth application-default login" in error


def test_recommendation_is_shown_as_sidebar_message_without_button(monkeypatch):
    monkeypatch.setattr(
        XaidaCopilot,
        "generate_recommendation",
        lambda self, session: "Review the flagged transactions next.",
    )
    app = _start_app()

    assert not app.exception
    assert not any(
        "recommendation" in button.label.lower()
        for button in app.button
    )
    assert any(
        "Welcome to XAIDA Vertex AI Assistant!" in item.value
        and "Upload an audit dataset" in item.value
        for item in app.info
    )
    about_section = next(
        expander for expander in app.expander
        if expander.label == "About & feedback"
    )
    assert (
        "XAIDA Project Team (anonymous)"
        in about_section.children[0].value
    )
    assert (
        "Anonymous survey link coming soon"
        in about_section.children[2].value
    )


def test_copilot_recommendation_appears_automatically_for_current_stage(
    monkeypatch,
):
    monkeypatch.setattr(
        XaidaCopilot,
        "generate_recommendation",
        lambda self, session: "Review the flagged transactions next.",
    )
    app = _start_app()
    app.session_state["audit_session"].metadata["workflow_stage"] = "analysis"
    app = app.run(timeout=30)

    assert not app.exception
    assert any(
        "Review the flagged transactions next." in item.value
        for item in app.info
    )


def test_copilot_recommendation_refreshes_when_next_step_changes(monkeypatch):
    monkeypatch.setattr(
        XaidaCopilot,
        "generate_recommendation",
        lambda self, session: (
            f"{get_next_recommended_step(session)}: this is the next process."
        ),
    )
    app = _start_app()
    session = app.session_state["audit_session"]
    session.metadata["workflow_stage"] = "analysis"
    app = app.run(timeout=30)

    assert any("Run Analysis:" in item.value for item in app.info)

    session.analysis["analysis_complete"] = True
    app = app.run(timeout=30)

    assert not app.exception
    assert any("Open Explainability:" in item.value for item in app.info)


def test_audit_completion_hides_recommendation_and_confirms_chatbot_available(
    monkeypatch,
):
    def fail_recommendation(self, session):
        raise AssertionError("Recommendations are disabled after completion.")

    monkeypatch.setattr(
        XaidaCopilot,
        "generate_recommendation",
        fail_recommendation,
    )
    app = _start_app()
    app.session_state["audit_session"].metadata[
        "workflow_stage"
    ] = "audit_completion"
    app = app.run(timeout=30)

    assert not app.exception
    assert any(
        "Thank you for completing this audit." in item.value
        for item in app.markdown
    )
    assert any(
        "Audit Workflow Completed" in item.value
        for item in app.markdown
    )
    assert any(
        button.label == "Return to completed audit"
        for button in app.button
    )
    assert not any(
        item.value == "Recommendation"
        for item in app.subheader
    )
    app = app.button(key="close_audit_completion_dialog").click().run(
        timeout=30
    )
    assert not any(
        button.label == "Return to completed audit"
        for button in app.button
    )


def test_completion_dialog_is_not_shown_before_audit_completion():
    app = _start_app()

    assert not app.exception
    assert not any(
        button.label == "Return to completed audit"
        for button in app.button
    )


def test_audit_review_metrics_are_written_to_sqlite():
    app = _start_app()
    session = app.session_state["audit_session"]
    session.metadata["workflow_stage"] = "audit_review"
    session.dataset.update(
        {
            "loaded": True,
            "rows": 3,
            "columns": 3,
            "dataframe": pd.DataFrame(
                {
                    "Amount": [10, 20, 30],
                    "Anomaly Flag": [True, True, False],
                    "Risk Score": [0.9, 0.8, 0.1],
                    "Auditor Assessment": [
                        "Confirmed Anomaly",
                        None,
                        "Potential Finding",
                    ],
                    "Auditor Comment": ["checked", "", "review"],
                }
            ),
        }
    )
    session.review["records"] = session.dataset["dataframe"].copy()
    session.review["review_version"] = 1
    session.analysis["dataset_version"] = 1
    session.analysis["dataset_versions"] = {
        1: session.dataset["dataframe"].copy()
    }
    session.analysis["dataset_version_metadata"] = {
        1: {"stage": "Analysis", "action": "Anomaly Dataset Generated"}
    }
    app = app.run(timeout=30)

    assert not app.exception
    with sqlite3.connect(os.environ["XAIDA_EVALUATION_DB_PATH"]) as connection:
        metrics = connection.execute(
            """
            SELECT total_records, ai_flagged_records, auditor_identified,
                   unassessed_records, remaining_reviews, confirmed_anomalies,
                   requires_investigation, potential_findings, false_positives
            FROM audit_review_metrics
            WHERE audit_session_id = ? AND dataset_version = 1
            """,
            (session.metadata["session_id"],),
        ).fetchone()
    assert metrics == (3, 2, 1, 0, 1, 1, 0, 1, 0)


def test_audit_review_displays_explainability_enriched_dataset_version():
    app = _start_app()
    session = app.session_state["audit_session"]
    session.metadata["workflow_stage"] = "audit_review"
    session.analysis["dataset_version"] = 2
    session.analysis["explainability_version"] = 2
    session.analysis["dataset_versions"] = {
        2: pd.DataFrame(
            {
                "Amount": [10],
                "Anomaly Flag": [True],
                "Risk Score": [0.9],
                "Explainability Narrative": ["High amount"],
            }
        )
    }
    session.review["records"] = session.analysis["dataset_versions"][2].copy()
    session.review["review_version"] = 2
    app.session_state["active_tab"] = "Audit Review"

    app = app.run(timeout=30)

    assert not app.exception
    assert any(
        "Explainability-enriched dataset · V2" in item.value
        for item in app.caption
    )


def test_action_confirmation_and_result_use_modal_dialogs():
    app = _start_app()
    session = app.session_state["audit_session"]
    session.metadata["workflow_stage"] = "audit_review"
    session.analysis["dataset_version"] = 1
    session.analysis["dataset_versions"] = {
        1: pd.DataFrame(
            {
                "Amount": [10],
                "Anomaly Flag": [True],
                "Risk Score": [0.9],
                "Auditor Assessment": [None],
                "Auditor Comment": [""],
            }
        )
    }
    session.review["records"] = session.analysis["dataset_versions"][1].copy()
    session.review["review_version"] = 1
    app = app.run(timeout=30)

    app = next(
        button for button in app.button if button.label == "Manual Review"
    ).click().run(timeout=30)

    assert not app.exception
    assert any(
        button.label == "Enter manual review"
        for button in app.button
    )
    assert any(
        "classify flagged records individually" in item.value
        for item in app.warning
    )
    assert not session.review.get("manual_review_mode", False)

    app = next(
        button for button in app.button if button.label == "Enter manual review"
    ).click().run(timeout=30)

    assert not app.exception
    assert session.review["manual_review_mode"]
    assert any(
        "Manual review enabled." in item.value
        for item in app.success
    )
    assert any(button.label == "Close" for button in app.button)


def test_data_processing_hides_results_until_dataset_is_prepared():
    app = _start_app()
    app.session_state["active_tab"] = "Data Processing"
    app = app.run(timeout=30)

    assert not app.exception
    assert any(
        "Preparation results are not available yet" in item.value
        for item in app.info
    )
    assert not any("PCA" in item.value for item in app.markdown)
    assert not any(
        item.label == "Feature engineering details"
        for item in app.expander
    )


def test_reports_tab_remains_selected_after_audit_completion():
    app = _start_app()
    session = app.session_state["audit_session"]
    session.metadata["workflow_stage"] = "reporting"
    session.analysis["report_generated"] = True
    session.reporting["pdf_ready"] = True
    session.reporting["excel_ready"] = True
    app = app.run(timeout=30)

    session.metadata["workflow_stage"] = "audit_completion"
    app = app.run(timeout=30)

    assert not app.exception
    assert app.session_state["active_tab"] == "Reports"
    assert any(
        element.value == "Audit reports"
        for element in app.subheader
    )


def test_lineage_tables_have_download_buttons():
    app = _start_app()
    session = app.session_state["audit_session"]
    session.analysis["dataset_versions"] = {
        1: pd.DataFrame({"Amount": [10, 20]}),
    }
    session.analysis["dataset_version_metadata"] = {
        1: {
            "stage": "Dataset Upload",
            "action": "Dataset Upload",
        },
    }
    app.session_state["active_tab"] = "Lineage"
    app = app.run(timeout=30)

    assert not app.exception
    download_labels = [
        button.label
        for button in app.get("download_button")
    ]
    assert "Download Dataset Version History CSV" in download_labels
    assert "Download Dataset Version V1 CSV" in download_labels


def test_evidence_progress_statuses_follow_stage_tab_order():
    app = _start_app()

    assert not app.exception
    status_chips = [
        item.value
        for item in app.caption
        if "-badge[" in item.value
    ]
    tab_names = [
        "Dataset",
        "Data Processing",
        "Duplicate Review",
        "Anomaly Detection",
        "Explainability",
        "Audit Review",
        "Findings",
        "Reports",
        "Lineage",
        "Audit Trail",
    ]
    assert len(status_chips) == len(tab_names)
    assert all(
        tab_name in chip
        for tab_name, chip in zip(tab_names, status_chips)
    )
    assert "Dataset: In progress" in status_chips[0]
    assert all(
        "Pending" in chip
        for chip in status_chips[1:8]
    )
    assert all(
        "Evidence" in chip
        for chip in status_chips[8:]
    )
    stage_selector = app.get("button_group")
    assert len(stage_selector) == 1
    assert stage_selector[0].options == tab_names
    assert not any(
        item.value == "Progression"
        for item in app.subheader
    )
    assert [item.label for item in app.expander][0] == (
        "Readiness score breakdown"
    )
    assert any(
        item.label == "Audit readiness"
        for item in app.metric
    )
    assert not any(
        item.value.startswith("Status:")
        or item.value.startswith("Explainability:")
        for item in app.caption
    )


def test_empty_dataset_view_guides_user_to_sidebar_controls():
    app = _start_app()

    assert not app.exception
    assert any(
        item.value == "Start with a dataset"
        for item in app.subheader
    )
    assert any(
        "Upload an audit dataset to begin reviewing records"
        in item.value
        for item in app.markdown
    )
    assert any(
        "dataset upload or sample dataset controls in the sidebar"
        in item.value
        for item in app.caption
    )


def test_evidence_tabs_render_before_their_workflow_data_is_available():
    app = _start_app()
    tab_names = [
        "Data Processing",
        "Duplicate Review",
        "Anomaly Detection",
        "Explainability",
        "Audit Review",
        "Findings",
        "Reports",
        "Lineage",
        "Audit Trail",
    ]

    for tab_name in tab_names:
        app.session_state["active_tab"] = tab_name
        app = app.run(timeout=30)
        assert not app.exception, f"{tab_name} raised an exception"
