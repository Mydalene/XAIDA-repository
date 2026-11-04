import sqlite3
import uuid

import assistant.evaluation_migration as evaluation_migration
import assistant.evaluation_store as evaluation_store


def test_sqlite_evaluation_migration_is_idempotent_and_keeps_source(
    tmp_path,
    monkeypatch,
):
    source_path = tmp_path / "source.sqlite3"
    destination_path = tmp_path / "destination.sqlite3"
    monkeypatch.setenv("XAIDA_DATABASE_BACKEND", "sqlite")
    monkeypatch.setenv(
        "XAIDA_EVALUATION_DB_PATH",
        str(source_path),
    )
    interaction_id = str(uuid.uuid4())
    evaluation_store.record_interaction(
        interaction_id=interaction_id,
        evaluation_session_id=str(uuid.uuid4()),
        workflow_stage="analysis",
        response_category="audit_status",
        latency_ms=25,
        outcome="success",
    )
    evaluation_store.record_audit_review_metrics(
        audit_session_id=str(uuid.uuid4()),
        dataset_version=1,
        metrics={
            "total_records": 10,
            "ai_flagged_records": 2,
            "auditor_identified": 1,
            "unassessed_records": 1,
            "remaining_reviews": 1,
            "confirmed_anomalies": 1,
            "requires_investigation": 0,
            "potential_findings": 0,
            "false_positives": 0,
        },
    )

    monkeypatch.setenv("XAIDA_DATABASE_BACKEND", "postgres")
    monkeypatch.setenv(
        "XAIDA_EVALUATION_DB_PATH",
        str(destination_path),
    )
    monkeypatch.setattr(
        evaluation_migration,
        "database_backend",
        lambda: "postgres",
    )
    monkeypatch.setattr(
        evaluation_migration,
        "parameter_placeholder",
        lambda: "?",
    )
    monkeypatch.setattr(
        evaluation_store,
        "parameter_placeholder",
        lambda: "?",
    )
    monkeypatch.setattr(
        evaluation_store,
        "connect_database",
        lambda: sqlite3.connect(destination_path),
    )

    first = evaluation_migration.migrate_sqlite_evaluations(source_path)
    second = evaluation_migration.migrate_sqlite_evaluations(source_path)

    with sqlite3.connect(destination_path) as connection:
        migrated_interaction = connection.execute(
            "SELECT interaction_id FROM interaction_evaluations"
        ).fetchone()
        metric_count = connection.execute(
            "SELECT COUNT(*) FROM audit_review_metrics"
        ).fetchone()[0]
    with sqlite3.connect(source_path) as connection:
        source_count = connection.execute(
            "SELECT COUNT(*) FROM interaction_evaluations"
        ).fetchone()[0]

    assert first == {"interactions": 1, "metrics": 1}
    assert second == {"interactions": 0, "metrics": 0}
    assert migrated_interaction == (interaction_id,)
    assert metric_count == 1
    assert source_count == 1
