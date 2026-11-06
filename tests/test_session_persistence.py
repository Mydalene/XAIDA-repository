import sqlite3
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

import assistant.evaluation_store as evaluation_store
import assistant.session_persistence as session_persistence
from assistant.session_manager import create_audit_session


@pytest.fixture
def cloud_store(tmp_path, monkeypatch):
    database_path = tmp_path / "xaida.sqlite3"
    objects = {}

    def connect():
        return sqlite3.connect(database_path)

    monkeypatch.setenv("XAIDA_SESSION_STORAGE_BACKEND", "gcs")
    monkeypatch.setenv("XAIDA_SESSION_STORAGE_BUCKET", "xaida-storage")
    monkeypatch.setenv("XAIDA_DATABASE_BACKEND", "postgres")
    monkeypatch.setenv("XAIDA_EVALUATION_DB_PATH", str(database_path))
    monkeypatch.setattr(session_persistence, "connect_database", connect)
    monkeypatch.setattr(
        session_persistence,
        "parameter_placeholder",
        lambda: "?",
    )
    monkeypatch.setattr(evaluation_store, "connect_database", connect)
    monkeypatch.setattr(
        evaluation_store,
        "parameter_placeholder",
        lambda: "?",
    )
    monkeypatch.setattr(
        session_persistence,
        "upload_bytes",
        lambda name, contents, content_type: objects.__setitem__(
            name, contents
        ),
    )
    monkeypatch.setattr(
        session_persistence,
        "download_bytes",
        lambda name: objects.get(name),
    )
    monkeypatch.setattr(
        session_persistence,
        "delete_prefix",
        lambda prefix: [
            objects.pop(name)
            for name in list(objects)
            if name.startswith(prefix)
        ],
    )
    return database_path, objects


def test_session_round_trips_dataset_and_analysis_types(cloud_store):
    _, objects = cloud_store
    session = create_audit_session()
    session.dataset["dataframe"] = pd.DataFrame(
        {
            "Amount": [12.5, 25.0],
            "Vendor": ["North", "South"],
            "Created": pd.Series(
                [
                    pd.Timestamp("2026-11-03 12:34:56.123456"),
                    pd.Timestamp("2026-11-04 01:02:03.654321"),
                ],
                dtype="datetime64[us]",
                index=[4, 9],
            ),
        },
        index=[4, 9],
    )
    session.dataset["default_index"] = pd.DataFrame(
        {"Count": pd.Series([1, 2], dtype="Int64")}
    )
    session.dataset["multi_index"] = pd.DataFrame(
        {"Flag": [True, False]},
        index=pd.MultiIndex.from_tuples(
            [("North", 1), ("South", 2)],
            names=["region", "row"],
        ),
    )
    session.analysis["risk_scores"] = np.asarray([0.25, 0.75])
    session.metadata["saved_at"] = datetime(
        2026,
        11,
        3,
        tzinfo=timezone.utc,
    )
    session.analysis["version_key"] = (1, "analysis")

    session_persistence.save_audit_session(session, "Auditor@Example.com")
    restored = session_persistence.load_audit_session(
        session.metadata["session_id"],
        "auditor@example.com",
    )

    pd.testing.assert_frame_equal(
        restored.dataset["dataframe"],
        session.dataset["dataframe"],
    )
    assert (
        str(restored.dataset["dataframe"]["Created"].dtype)
        == "datetime64[us]"
    )
    pd.testing.assert_frame_equal(
        restored.dataset["default_index"],
        session.dataset["default_index"],
    )
    pd.testing.assert_frame_equal(
        restored.dataset["multi_index"],
        session.dataset["multi_index"],
    )
    np.testing.assert_array_equal(
        restored.analysis["risk_scores"],
        session.analysis["risk_scores"],
    )
    assert restored.metadata["saved_at"] == session.metadata["saved_at"]
    assert restored.analysis["version_key"] == (1, "analysis")
    assert len(objects) == 1


def test_audit_session_is_bound_to_the_signed_in_auditor(cloud_store):
    _, objects = cloud_store
    session = create_audit_session()
    session_persistence.save_audit_session(session, "owner@example.com")

    with pytest.raises(
        session_persistence.SessionUnavailableError,
        match="unavailable",
    ):
        session_persistence.load_audit_session(
            session.metadata["session_id"],
            "another@example.com",
        )

    assert objects


def test_expired_session_is_deleted_without_deleting_evaluation_records(
    cloud_store,
):
    database_path, objects = cloud_store
    session = create_audit_session()
    session_id = session.metadata["session_id"]
    session_persistence.save_audit_session(session, "owner@example.com")
    evaluation_store.record_interaction(
        interaction_id="evaluation-kept",
        evaluation_session_id=session.evaluation_session_id,
        workflow_stage="analysis",
        response_category="audit_status",
        latency_ms=10,
        outcome="success",
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE xaida_audit_sessions SET expires_at = ? "
            "WHERE session_id = ?",
            (
                (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
                session_id,
            ),
        )

    with pytest.raises(
        session_persistence.SessionExpiredError,
        match="24 hours",
    ):
        session_persistence.load_audit_session(
            session_id,
            "owner@example.com",
        )

    with sqlite3.connect(database_path) as connection:
        session_row = connection.execute(
            "SELECT session_id FROM xaida_audit_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        evaluation_row = connection.execute(
            "SELECT interaction_id FROM interaction_evaluations "
            "WHERE interaction_id = ?",
            ("evaluation-kept",),
        ).fetchone()
    assert session_row is None
    assert evaluation_row == ("evaluation-kept",)
    assert not objects


def test_delete_session_removes_all_session_objects_and_metadata(cloud_store):
    database_path, objects = cloud_store
    session = create_audit_session()
    session_id = session.metadata["session_id"]
    session_persistence.save_audit_session(session, "owner@example.com")
    objects[f"audit-sessions/{session_id}/models/model.joblib"] = b"model"

    assert session_persistence.delete_audit_session(
        session_id,
        "owner@example.com",
    )

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT session_id FROM xaida_audit_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    assert row is None
    assert not objects


def test_unsupported_session_values_fail_instead_of_being_dropped():
    with pytest.raises(TypeError, match="Unsupported audit-session value"):
        session_persistence._encode(object())


def test_encode_uses_snapshot_when_dictionary_changes_during_encoding(
    monkeypatch,
):
    source = {"first": "value"}
    original_encode = session_persistence._encode

    def mutate_during_encode(value):
        if value == "value":
            source["added during encoding"] = "new value"
        return original_encode(value)

    monkeypatch.setattr(
        session_persistence,
        "_encode",
        mutate_during_encode,
    )

    encoded = session_persistence._encode(source)

    assert encoded == {
        "__xaida_type__": "dict",
        "items": [["first", "value"]],
    }
    assert source["added during encoding"] == "new value"


def test_expired_session_cleanup_removes_metadata_and_objects(cloud_store):
    database_path, objects = cloud_store
    session = create_audit_session()
    session_id = session.metadata["session_id"]
    session_persistence.save_audit_session(session, "owner@example.com")
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE xaida_audit_sessions SET expires_at = ? "
            "WHERE session_id = ?",
            (
                (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
                session_id,
            ),
        )

    assert session_persistence.delete_expired_sessions() == 1
    assert not objects
