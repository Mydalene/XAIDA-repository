import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from assistant.evaluation_store import (
    DEFAULT_DB_PATH,
    _connect,
    _retention_days,
)
from core.database import database_backend, parameter_placeholder

INTERACTION_COLUMNS = (
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
)

METRIC_COLUMNS = (
    "audit_session_id",
    "dataset_version",
    "captured_at",
    "total_records",
    "ai_flagged_records",
    "auditor_identified",
    "unassessed_records",
    "remaining_reviews",
    "confirmed_anomalies",
    "requires_investigation",
    "potential_findings",
    "false_positives",
)


def _read_table(connection, table, columns):
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    if not exists:
        return []
    actual_columns = tuple(
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})")
    )
    if actual_columns != columns:
        raise ValueError(
            f"SQLite table {table!r} does not match the supported schema."
        )
    selected_columns = ", ".join(columns)
    return connection.execute(
        f"SELECT {selected_columns} FROM {table}"
    ).fetchall()


def migrate_sqlite_evaluations(source_path=DEFAULT_DB_PATH):
    if database_backend() != "postgres":
        raise RuntimeError(
            "Set XAIDA_DATABASE_BACKEND=postgres before migrating "
            "evaluation data."
        )

    source_path = Path(source_path).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(
            f"The SQLite evaluation database was not found: {source_path}"
        )

    source_uri = f"{source_path.as_uri()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as source:
        interactions = _read_table(
            source,
            "interaction_evaluations",
            INTERACTION_COLUMNS,
        )
        metrics = _read_table(
            source,
            "audit_review_metrics",
            METRIC_COLUMNS,
        )

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=_retention_days())
    ).isoformat()
    interactions = [
        row for row in interactions if row[2] >= cutoff
    ]
    metrics = [
        row for row in metrics if row[2] >= cutoff
    ]
    if not interactions and not metrics:
        return {"interactions": 0, "metrics": 0}

    marker = parameter_placeholder()
    interaction_markers = ", ".join(
        marker for _ in INTERACTION_COLUMNS
    )
    metric_markers = ", ".join(marker for _ in METRIC_COLUMNS)
    try:
        with _connect() as destination:
            cursor = destination.cursor()
            cursor.executemany(
                f"""
                INSERT INTO interaction_evaluations (
                    {", ".join(INTERACTION_COLUMNS)}
                ) VALUES ({interaction_markers})
                ON CONFLICT (interaction_id) DO NOTHING
                """,
                interactions,
            )
            interaction_count = cursor.rowcount
            cursor.executemany(
                f"""
                INSERT INTO audit_review_metrics (
                    {", ".join(METRIC_COLUMNS)}
                ) VALUES ({metric_markers})
                ON CONFLICT (audit_session_id, dataset_version) DO NOTHING
                """,
                metrics,
            )
            metrics_count = cursor.rowcount
    except Exception as error:
        raise RuntimeError(
            "Evaluation migration failed. The source SQLite file was not "
            "modified; verify the destination schema and connectivity."
        ) from error

    return {
        "interactions": interaction_count,
        "metrics": metrics_count,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the existing SQLite evaluation database.",
    )
    args = parser.parse_args()
    counts = migrate_sqlite_evaluations(args.source)
    print(
        "Migrated "
        f"{counts['interactions']} interaction rows and "
        f"{counts['metrics']} aggregate metric rows."
    )


if __name__ == "__main__":
    main()
