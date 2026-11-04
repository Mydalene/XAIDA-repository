import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.app_metadata import APP_VERSION
from core.database import connect_database, parameter_placeholder

GROUNDING_RATINGS = (
    "Grounded",
    "Potentially unsupported",
    "Unsure",
)

DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "xaida_evaluations.sqlite3"
)


def _retention_days():
    raw_days = os.getenv("XAIDA_EVALUATION_RETENTION_DAYS", "365")
    try:
        retention_days = int(raw_days)
    except ValueError as error:
        raise ValueError(
            "XAIDA_EVALUATION_RETENTION_DAYS must be a positive integer."
        ) from error
    if retention_days <= 0:
        raise ValueError(
            "XAIDA_EVALUATION_RETENTION_DAYS must be a positive integer."
        )
    return retention_days


def _connect():
    retention_days = _retention_days()
    connection = connect_database()
    marker = parameter_placeholder()
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS interaction_evaluations (
            interaction_id TEXT PRIMARY KEY,
            evaluation_session_id TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            workflow_stage TEXT NOT NULL,
            response_category TEXT NOT NULL,
            latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
            outcome TEXT NOT NULL CHECK (outcome IN ('success', 'error')),
            error_category TEXT,
            grounding_rating TEXT CHECK (
                grounding_rating IS NULL
                OR grounding_rating IN (
                    'Grounded',
                    'Potentially unsupported',
                    'Unsure'
                )
            ),
            helpfulness_rating INTEGER CHECK (
                helpfulness_rating IS NULL
                OR helpfulness_rating BETWEEN 1 AND 5
            ),
            app_version TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_review_metrics (
            audit_session_id TEXT NOT NULL,
            dataset_version INTEGER NOT NULL CHECK (dataset_version > 0),
            captured_at TEXT NOT NULL,
            total_records INTEGER NOT NULL CHECK (total_records >= 0),
            ai_flagged_records INTEGER NOT NULL CHECK (ai_flagged_records >= 0),
            auditor_identified INTEGER NOT NULL CHECK (auditor_identified >= 0),
            unassessed_records INTEGER NOT NULL CHECK (unassessed_records >= 0),
            remaining_reviews INTEGER NOT NULL CHECK (remaining_reviews >= 0),
            confirmed_anomalies INTEGER NOT NULL CHECK (confirmed_anomalies >= 0),
            requires_investigation INTEGER NOT NULL CHECK (
                requires_investigation >= 0
            ),
            potential_findings INTEGER NOT NULL CHECK (potential_findings >= 0),
            false_positives INTEGER NOT NULL CHECK (false_positives >= 0),
            PRIMARY KEY (audit_session_id, dataset_version)
        )
        """
    )
    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(days=retention_days)
    ).isoformat()
    connection.execute(
        "DELETE FROM interaction_evaluations WHERE occurred_at < "
        f"{marker}",
        (cutoff,),
    )
    connection.execute(
        "DELETE FROM audit_review_metrics WHERE captured_at < "
        f"{marker}",
        (cutoff,),
    )
    return connection


def record_audit_review_metrics(
    *,
    audit_session_id,
    dataset_version,
    metrics,
):
    if not isinstance(audit_session_id, str) or not audit_session_id.strip():
        raise ValueError("Audit session ID is required.")
    if (
        not isinstance(dataset_version, int)
        or isinstance(dataset_version, bool)
        or dataset_version <= 0
    ):
        raise ValueError("Dataset version must be a positive integer.")

    metric_fields = (
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
    if not isinstance(metrics, dict) or set(metrics) != set(metric_fields):
        raise ValueError("Audit review metrics do not match the required fields.")
    for field in metric_fields:
        value = metrics[field]
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
        ):
            raise ValueError(f"{field} must be a non-negative integer.")

    captured_at = datetime.now(timezone.utc).isoformat()
    fields = ", ".join(metric_fields)
    marker = parameter_placeholder()
    placeholders = ", ".join(
        marker for _ in range(len(metric_fields) + 3)
    )
    updates = ", ".join(
        f"{field} = excluded.{field}"
        for field in ("captured_at", *metric_fields)
    )
    with _connect() as connection:
        connection.execute(
            f"""
            INSERT INTO audit_review_metrics (
                audit_session_id,
                dataset_version,
                captured_at,
                {fields}
            ) VALUES ({placeholders})
            ON CONFLICT (audit_session_id, dataset_version)
            DO UPDATE SET {updates}
            """,
            (
                audit_session_id,
                dataset_version,
                captured_at,
                *(metrics[field] for field in metric_fields),
            ),
        )


def record_interaction(
    *,
    interaction_id,
    evaluation_session_id,
    workflow_stage,
    response_category,
    latency_ms,
    outcome,
    error_category=None,
):
    if outcome not in {"success", "error"}:
        raise ValueError("Invalid interaction outcome.")
    if latency_ms < 0:
        raise ValueError("Interaction latency cannot be negative.")
    if outcome == "success" and error_category is not None:
        raise ValueError("Successful interactions cannot have an error category.")

    occurred_at = datetime.now(timezone.utc).isoformat()
    marker = parameter_placeholder()
    with _connect() as connection:
        connection.execute(
            f"""
            INSERT INTO interaction_evaluations (
                interaction_id,
                evaluation_session_id,
                occurred_at,
                workflow_stage,
                response_category,
                latency_ms,
                outcome,
                error_category,
                app_version
            ) VALUES (
                {marker}, {marker}, {marker}, {marker}, {marker},
                {marker}, {marker}, {marker}, {marker}
            )
            """,
            (
                interaction_id,
                evaluation_session_id,
                occurred_at,
                workflow_stage,
                response_category,
                latency_ms,
                outcome,
                error_category,
                APP_VERSION,
            ),
        )


def record_feedback(
    *,
    interaction_id,
    grounding_rating,
    helpfulness_rating,
):
    if grounding_rating not in GROUNDING_RATINGS:
        raise ValueError("Select a valid response-grounding rating.")
    if (
        not isinstance(helpfulness_rating, int)
        or isinstance(helpfulness_rating, bool)
        or not 1 <= helpfulness_rating <= 5
    ):
        raise ValueError("Helpfulness rating must be between 1 and 5.")

    marker = parameter_placeholder()
    with _connect() as connection:
        cursor = connection.execute(
            f"""
            UPDATE interaction_evaluations
            SET grounding_rating = {marker}, helpfulness_rating = {marker}
            WHERE interaction_id = {marker} AND outcome = 'success'
            """,
            (
                grounding_rating,
                helpfulness_rating,
                interaction_id,
            ),
        )
        if cursor.rowcount != 1:
            raise ValueError(
                "The XAIDA response could not be found for evaluation."
            )
