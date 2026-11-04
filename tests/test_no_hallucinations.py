import json

import pytest

import assistant.copilot as copilot_module
from assistant.copilot import XaidaCopilot
from assistant.session_manager import create_audit_session


class RecordingClient:
    def __init__(self):
        self.request = None

    def generate_content(self, messages):
        self.request = messages
        return "Deterministic test response."


@pytest.fixture
def empty_session():
    session = create_audit_session()
    session.metadata["workflow_stage"] = "analysis"
    return session


def ask_with_recording_client(session, question):
    copilot = XaidaCopilot()
    client = RecordingClient()
    copilot.client = client

    response = copilot.chat(session, question)

    assert response == "Deterministic test response."
    return client.request


def get_evidence_snapshot(messages):
    snapshot_message = next(
        message["content"]
        for message in messages
        if message["content"].startswith(
            "Complete audit evidence snapshot"
        )
    )
    _, _, snapshot_json = snapshot_message.partition("\n")
    return json.loads(snapshot_json)


def assert_grounding_instructions(messages):
    system_prompt = "\n".join(
        message["content"]
        for message in messages
        if message["role"] == "system"
    )
    normalized_prompt = " ".join(system_prompt.split())
    assert "Never infer:" in normalized_prompt
    assert "Only report information supported by" in normalized_prompt
    assert (
        "Methodology fields describe configured or documented behavior, "
        "not necessarily behavior executed for the current audit."
        in normalized_prompt
    )


def test_missing_analysis_results_are_distinguished_from_configured_method(
    empty_session,
):
    empty_session.analysis.clear()

    messages = ask_with_recording_client(
        empty_session,
        "What anomaly detection algorithms were used?",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["analysis_complete"] is False
    assert snapshot["threshold"] is None
    assert snapshot["analysis_engine"] == "Ensemble Detection"
    assert_grounding_instructions(messages)


def test_threshold_methodology_does_not_imply_a_threshold_was_calculated(
    empty_session,
):
    empty_session.analysis.clear()

    messages = ask_with_recording_client(
        empty_session,
        "How is the anomaly threshold determined?",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["threshold"] is None
    assert snapshot["threshold_method"] == "Dynamic Quantile Threshold"
    assert snapshot["analysis_complete"] is False
    assert_grounding_instructions(messages)


def test_missing_findings_are_explicit_in_the_evidence_snapshot(
    empty_session,
):
    empty_session.findings.clear()

    messages = ask_with_recording_client(
        empty_session,
        "What evidence supports Finding 1?",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["findings_available"] is False
    assert snapshot["findings_register"] == []
    assert snapshot["total_findings"] == 0
    assert_grounding_instructions(messages)


def test_configured_explainability_engine_is_distinguished_from_execution(
    empty_session,
):
    empty_session.explainability.clear()

    messages = ask_with_recording_client(
        empty_session,
        "What explainability engine was used?",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["explainability_engine"] == "SHAP"
    assert snapshot["analysis_complete"] is False
    assert snapshot["explained_record_count"] == 0
    assert snapshot["shap_contribution_details"] == []
    assert_grounding_instructions(messages)


def test_missing_selected_transaction_is_explicit(
    empty_session,
):
    empty_session.explainability.clear()

    messages = ask_with_recording_client(
        empty_session,
        "Explain the selected transaction.",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["selected_transaction"] == {}
    assert snapshot["selected_record"] is None
    assert_grounding_instructions(messages)


def test_missing_duplicate_decision_is_explicit(
    empty_session,
):
    empty_session.duplicates.clear()

    messages = ask_with_recording_client(
        empty_session,
        "What duplicate strategy was applied?",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["duplicate_strategy"] is None
    assert snapshot["duplicate_count"] == 0
    assert snapshot["duplicate_review_complete"] is False
    assert_grounding_instructions(messages)


def test_default_imputation_rules_are_not_mistaken_for_applied_treatment(
    empty_session,
):
    empty_session.dataset.clear()

    messages = ask_with_recording_client(
        empty_session,
        "What are the default imputation rules?",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["default_imputation_rules"]["numeric"]["strategy"] == (
        "median"
    )
    assert snapshot["imputation_log"] == []
    assert snapshot["dataset_name"] is None
    assert_grounding_instructions(messages)


def test_empty_audit_history_is_explicit(
    empty_session,
):
    empty_session.audit_log.clear()
    empty_session.analysis["dataset_version_metadata"] = {}

    messages = ask_with_recording_client(
        empty_session,
        "Summarise this audit.",
    )
    snapshot = get_evidence_snapshot(messages)

    assert snapshot["audit_entry_count"] == 0
    assert snapshot["audit_timeline"] == []
    assert snapshot["dataset_version_history"] == []
    assert_grounding_instructions(messages)


def test_recommendation_uses_audit_status_and_briefly_explains_the_process(
    empty_session,
    monkeypatch,
):
    context = {
        "workflow_stage": "analysis",
        "next_recommended_step": "Run Analysis",
        "audit_readiness_score": 72,
        "analysis_complete": False,
        "flagged_transaction_count": 0,
        "dataset_name": "sensitive-detail.csv",
        "flagged_transaction_details": [{"Account": "123456"}],
    }
    monkeypatch.setattr(
        copilot_module,
        "build_context",
        lambda session: context,
    )
    copilot = XaidaCopilot()
    client = RecordingClient()
    copilot.client = client

    recommendation = copilot.generate_recommendation(empty_session)

    messages = client.request
    recommendation_request = json.loads(
        messages[1]["content"].partition("audit status:\n")[2]
    )
    system_prompt = messages[0]["content"]

    assert recommendation == "Deterministic test response."
    assert recommendation_request == {
        "workflow_stage": "analysis",
        "next_recommended_step": "Run Analysis",
        "audit_readiness_score": 72,
        "analysis_complete": False,
        "flagged_transaction_count": 0,
    }
    assert "one short, actionable next step" in system_prompt
    assert "one brief sentence explaining what that process does" in (
        system_prompt
    )
    assert "any extra recommendations" in system_prompt
