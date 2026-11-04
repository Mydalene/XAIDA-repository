# ============================================================
# Evidence Grounding Tests
# ============================================================

import pytest

from assistant.vertex_ai_assistant import XaidaVertexAIAssistant
from assistant.session_manager import (
    create_audit_session,
)


class _RecordingCompletions:
    def generate_content(self, messages):
        return (
            "The audit context does not contain evidence "
            "supporting this request."
        )


@pytest.fixture(autouse=True)
def prevent_external_ai_requests(monkeypatch):
    client = _RecordingCompletions()
    monkeypatch.setattr(
        XaidaVertexAIAssistant,
        "_get_completion_client",
        lambda self: client,
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
# HELPERS
# ============================================================

def contains_fabrication_language(
    response,
):

    response = response.lower()

    forbidden = [
        "i assume",
        "probably",
        "likely",
        "might have",
        "could have",
        "appears that",
        "i think",
        "i believe",
        "presumably",
    ]

    return any(
        term in response
        for term in forbidden
    )

def test_no_fabricated_finding_evidence(
    empty_session,
):

    empty_session.findings.clear()

    vertex_ai_assistant = XaidaVertexAIAssistant()

    response = vertex_ai_assistant.chat(
        empty_session,
        "What evidence supports Finding 1?"
    )

    assert not contains_fabrication_language(
        response
    )

    assert (
        "invoice"
        not in response.lower()
    )

    assert (
        "payment"
        not in response.lower()
    )

def test_no_fabricated_traceability(
    empty_session,
):

    empty_session.findings.clear()

    vertex_ai_assistant = XaidaVertexAIAssistant()

    response = vertex_ai_assistant.chat(
        empty_session,
        "Trace Finding 1 to its source."
    )

    assert not contains_fabrication_language(
        response
    )

def test_no_fabricated_audit_history(
    empty_session,
):

    empty_session.audit_log.clear()

    vertex_ai_assistant = XaidaVertexAIAssistant()

    response = vertex_ai_assistant.chat(
        empty_session,
        "Summarise the audit history."
    )

    assert not contains_fabrication_language(
        response
    )

    assert (
        "dataset uploaded"
        not in response.lower()
    )

def test_no_fabricated_lineage(
    empty_session,
):

    empty_session.analysis[
        "dataset_version_metadata"
    ] = {}

    vertex_ai_assistant = XaidaVertexAIAssistant()

    response = vertex_ai_assistant.chat(
        empty_session,
        "Explain dataset version history."
    )

    assert not contains_fabrication_language(
        response
    )

def test_no_fabricated_transaction_explanation(
    empty_session,
):

    empty_session.explainability.clear()

    vertex_ai_assistant = XaidaVertexAIAssistant()

    response = vertex_ai_assistant.chat(
        empty_session,
        "Explain the selected transaction."
    )

    assert not contains_fabrication_language(
        response
    )

    assert (
        "invoice"
        not in response.lower()
    )

def test_no_fabricated_duplicate_results(
    empty_session,
):

    empty_session.duplicates.clear()

    vertex_ai_assistant = XaidaVertexAIAssistant()

    response = vertex_ai_assistant.chat(
        empty_session,
        "Which records were removed?"
    )

    assert not contains_fabrication_language(
        response
    )
