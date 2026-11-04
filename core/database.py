import os
import sqlite3
from pathlib import Path


def database_backend():
    backend = os.getenv("XAIDA_DATABASE_BACKEND", "sqlite").strip().casefold()
    if backend not in {"sqlite", "postgres"}:
        raise RuntimeError(
            "XAIDA_DATABASE_BACKEND must be 'sqlite' or 'postgres'."
        )
    return backend


def parameter_placeholder():
    return "%s" if database_backend() == "postgres" else "?"


def connect_database():
    backend = database_backend()
    session_backend = os.getenv(
        "XAIDA_SESSION_STORAGE_BACKEND",
        "local",
    ).strip().casefold()
    if session_backend == "gcs" and backend != "postgres":
        raise RuntimeError(
            "Cloud Storage audit sessions require XAIDA_DATABASE_BACKEND="
            "'postgres' so session ownership and evaluation records are "
            "durable."
        )
    if backend == "sqlite":
        default_path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "xaida_evaluations.sqlite3"
        )
        database_path = Path(
            os.getenv("XAIDA_EVALUATION_DB_PATH", str(default_path))
        )
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(database_path, timeout=30)

    required_settings = {
        "CLOUD_SQL_CONNECTION_NAME": os.getenv(
            "CLOUD_SQL_CONNECTION_NAME", ""
        ).strip(),
        "XAIDA_DATABASE_NAME": os.getenv(
            "XAIDA_DATABASE_NAME", ""
        ).strip(),
        "XAIDA_DATABASE_USER": os.getenv(
            "XAIDA_DATABASE_USER", ""
        ).strip(),
        "XAIDA_DATABASE_PASSWORD": os.getenv(
            "XAIDA_DATABASE_PASSWORD", ""
        ),
    }
    missing_settings = [
        setting
        for setting, value in required_settings.items()
        if not value
    ]
    if missing_settings:
        raise RuntimeError(
            "XAIDA PostgreSQL is not configured. Set the required "
            f"environment variables: {', '.join(missing_settings)}."
        )

    host = os.getenv("XAIDA_DATABASE_HOST", "").strip()
    if not host:
        host = f"/cloudsql/{required_settings['CLOUD_SQL_CONNECTION_NAME']}"

    try:
        import psycopg
    except ImportError as error:
        raise RuntimeError(
            "PostgreSQL support is missing. Install the project requirements."
        ) from error

    return psycopg.connect(
        host=host,
        dbname=required_settings["XAIDA_DATABASE_NAME"],
        user=required_settings["XAIDA_DATABASE_USER"],
        password=required_settings["XAIDA_DATABASE_PASSWORD"],
        connect_timeout=10,
    )
