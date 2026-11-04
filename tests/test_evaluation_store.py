import sqlite3
import uuid

import pytest

from assistant.conversation_manager import add_assistant_message
from assistant.copilot import XaidaCopilot
from assistant.evaluation_store import (
    record_audit_review_metrics,
    record_feedback,
)
from assistant.session_manager import create_audit_session


def _read_events(database_path):
    with sqlite3.connect(database_path) as connection:
        columns = [
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(interaction_evaluations)"
            )
        ]
        rows = connection.execute(
            "SELECT * FROM interaction_evaluations"
        ).fetchall()
    return columns, rows


def test_chat_event_and_feedback_store_only_allowlisted_metadata(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "evaluation.sqlite3"
    monkeypatch.setenv("XAIDA_EVALUATION_DB_PATH", str(database_path))
    session = create_audit_session()
    session.metadata["workflow_stage"] = "analysis"
    prompt = "Private prompt that must not be stored"
    response = "Private response that must not be stored"

    def fake_chat(self, chat_session, user_message):
        add_assistant_message(chat_session, response)
        return response

    monkeypatch.setattr(XaidaCopilot, "_chat", fake_chat)
    result = XaidaCopilot().chat(session, prompt)
    assistant_message = session.conversation[-1]

    record_feedback(
        interaction_id=assistant_message["interaction_id"],
        grounding_rating="Potentially unsupported",
        helpfulness_rating=2,
    )

    columns, rows = _read_events(database_path)
    assert result == response
    assert assistant_message["interaction_id"]
    assert {
        "interaction_id",
        "evaluation_session_id",
        "occurred_at",
        "workflow_stage",
        "response_category",
        "latency_ms",
        "outcome",
        "error_category",
        "grounding_rating",
        "helpfulness_rating",
        "app_version",
    } == set(columns)
    assert prompt not in repr(rows)
    assert response not in repr(rows)
    assert session.evaluation_session_id not in {"", session.metadata["session_id"]}
    assert rows[0][1] == session.evaluation_session_id
    assert rows[0][3] == "analysis"
    assert rows[0][6] == "success"
    assert rows[0][8] == "Potentially unsupported"
    assert rows[0][9] == 2
    assert rows[0][10] == "1.0"


def test_chat_failure_records_safe_category_without_exception_details(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "evaluation.sqlite3"
    monkeypatch.setenv("XAIDA_EVALUATION_DB_PATH", str(database_path))
    session = create_audit_session()

    def fail_chat(self, chat_session, user_message):
        raise RuntimeError("sensitive exception detail")

    monkeypatch.setattr(XaidaCopilot, "_chat", fail_chat)
    with pytest.raises(RuntimeError, match="sensitive exception detail"):
        XaidaCopilot().chat(session, "private question")

    _, rows = _read_events(database_path)
    assert len(rows) == 1
    assert rows[0][6] == "error"
    assert rows[0][7] == "ai_service_configuration"
    assert "sensitive exception detail" not in repr(rows)
    assert "private question" not in repr(rows)


def test_feedback_rejects_invalid_values_without_changing_event(
    monkeypatch,
    tmp_path,
):
    from assistant.evaluation_store import record_interaction

    database_path = tmp_path / "evaluation.sqlite3"
    monkeypatch.setenv("XAIDA_EVALUATION_DB_PATH", str(database_path))
    interaction_id = str(uuid.uuid4())
    record_interaction(
        interaction_id=interaction_id,
        evaluation_session_id=str(uuid.uuid4()),
        workflow_stage="analysis",
        response_category="audit_status",
        latency_ms=10,
        outcome="success",
    )

    with pytest.raises(ValueError, match="grounding rating"):
        record_feedback(
            interaction_id=interaction_id,
            grounding_rating="Not a rating",
            helpfulness_rating=3,
        )

    with sqlite3.connect(database_path) as connection:
        ratings = connection.execute(
            """
            SELECT grounding_rating, helpfulness_rating
            FROM interaction_evaluations
            WHERE interaction_id = ?
            """,
            (interaction_id,),
        ).fetchone()
    assert ratings == (None, None)


def test_audit_review_metrics_are_upserted_as_aggregates(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "evaluation.sqlite3"
    monkeypatch.setenv("XAIDA_EVALUATION_DB_PATH", str(database_path))
    audit_session_id = str(uuid.uuid4())
    metrics = {
        "total_records": 10,
        "ai_flagged_records": 4,
        "auditor_identified": 2,
        "unassessed_records": 1,
        "remaining_reviews": 2,
        "confirmed_anomalies": 1,
        "requires_investigation": 2,
        "potential_findings": 1,
        "false_positives": 1,
    }

    record_audit_review_metrics(
        audit_session_id=audit_session_id,
        dataset_version=3,
        metrics=metrics,
    )
    updated_metrics = {**metrics, "remaining_reviews": 1}
    record_audit_review_metrics(
        audit_session_id=audit_session_id,
        dataset_version=3,
        metrics=updated_metrics,
    )

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT audit_session_id, dataset_version, total_records,
                   ai_flagged_records, auditor_identified, unassessed_records,
                   remaining_reviews, confirmed_anomalies,
                   requires_investigation, potential_findings, false_positives
            FROM audit_review_metrics
            """
        ).fetchall()
    assert rows == [
        (
            audit_session_id,
            3,
            10,
            4,
            2,
            1,
            1,
            1,
            2,
            1,
            1,
        )
    ]
