import argparse
import io
import gzip
import hashlib
import json
import math
import os
import uuid
from datetime import date, datetime, time, timedelta, timezone

import numpy as np
import pandas as pd
import streamlit as st

from assistant.audit_session import AuditSession
from core.access_control import authenticated_user_email
from core.cloud_storage import (
    cloud_storage_enabled,
    delete_prefix,
    download_bytes,
    upload_bytes,
)
from core.database import connect_database, parameter_placeholder

SESSION_QUERY_PARAM = "audit_session_id"
SESSION_OBJECT_PREFIX = "audit-sessions"
SNAPSHOT_FORMAT_VERSION = 1
DEFAULT_RETENTION_HOURS = 24
MAX_SNAPSHOT_BYTES = 200 * 1024 * 1024
MAX_UNCOMPRESSED_SNAPSHOT_BYTES = 512 * 1024 * 1024


class SessionPersistenceError(RuntimeError):
    pass


class SessionExpiredError(SessionPersistenceError):
    pass


class SessionUnavailableError(SessionPersistenceError):
    pass


def session_storage_backend():
    return "gcs" if cloud_storage_enabled() else "local"


def session_storage_enabled():
    return session_storage_backend() == "gcs"


def _retention_hours():
    raw_hours = os.getenv(
        "XAIDA_SESSION_RETENTION_HOURS",
        str(DEFAULT_RETENTION_HOURS),
    )
    try:
        hours = int(raw_hours)
    except ValueError as error:
        raise ValueError(
            "XAIDA_SESSION_RETENTION_HOURS must be a positive integer."
        ) from error
    if hours <= 0:
        raise ValueError(
            "XAIDA_SESSION_RETENTION_HOURS must be a positive integer."
        )
    return hours


def _owner_hash(owner_email):
    if not isinstance(owner_email, str) or not owner_email.strip():
        raise SessionPersistenceError(
            "A signed-in auditor identity is required for saved audit data."
        )
    return hashlib.sha256(
        owner_email.strip().casefold().encode("utf-8")
    ).hexdigest()


def _authenticated_owner():
    email = authenticated_user_email()
    if not email:
        raise SessionPersistenceError(
            "Sign in before loading or saving audit data."
        )
    return email


def _object_prefix(session_id):
    return f"{SESSION_OBJECT_PREFIX}/{session_id}/"


def _session_object_name(session_id):
    return f"{_object_prefix(session_id)}session.json.gz"


def _encode_index(index):
    if isinstance(index, pd.RangeIndex):
        return {
            "kind": "range",
            "start": index.start,
            "stop": index.stop,
            "step": index.step,
            "name": _encode(index.name),
        }
    if isinstance(index, pd.MultiIndex):
        return {
            "kind": "multi",
            "values": _encode(list(index)),
            "names": _encode(index.names),
        }
    return {
        "kind": "index",
        "values": _encode(list(index)),
        "name": _encode(index.name),
        "dtype": str(index.dtype),
    }


def _decode_index(value):
    if value["kind"] == "range":
        return pd.RangeIndex(
            value["start"],
            value["stop"],
            value["step"],
            name=_decode(value["name"]),
        )
    if value["kind"] == "multi":
        return pd.MultiIndex.from_tuples(
            _decode(value["values"]),
            names=_decode(value["names"]),
        )
    try:
        return pd.Index(
            _decode(value["values"]),
            name=_decode(value["name"]),
            dtype=value["dtype"],
        )
    except (TypeError, ValueError) as error:
        raise SessionPersistenceError(
            f"Unsupported saved index dtype: {value['dtype']}."
        ) from error


def _encode(value):
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, pd.DataFrame):
        return {
            "__xaida_type__": "dataframe",
            "columns": _encode_index(value.columns),
            "index": _encode_index(value.index),
            "dtypes": [str(dtype) for dtype in value.dtypes],
            "data": _encode(
                [
                    list(row)
                    for row in value.itertuples(index=False, name=None)
                ]
            ),
        }
    if isinstance(value, pd.Series):
        return {
            "__xaida_type__": "series",
            "name": _encode(value.name),
            "index": _encode_index(value.index),
            "dtype": str(value.dtype),
            "data": _encode(value.tolist()),
        }
    if isinstance(value, np.ndarray):
        return {
            "__xaida_type__": "ndarray",
            "dtype": value.dtype.str,
            "shape": list(value.shape),
            "data": _encode(value.tolist()),
        }
    if isinstance(value, np.generic):
        return _encode(value.item())
    if isinstance(value, (datetime, date, time)):
        return {
            "__xaida_type__": type(value).__name__,
            "value": value.isoformat(),
        }
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        items = value.copy().items()
        return {
            "__xaida_type__": "dict",
            "items": [
                [_encode(key), _encode(item)]
                for key, item in items
            ],
        }
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, tuple):
        return {
            "__xaida_type__": "tuple",
            "items": [_encode(item) for item in value],
        }
    if isinstance(value, set):
        return {
            "__xaida_type__": "set",
            "items": [_encode(item) for item in sorted(value, key=repr)],
        }

    module = type(value).__module__
    if module.startswith("shap") and hasattr(value, "values"):
        return {
            "__xaida_type__": "shap_explanation",
            "values": _encode(value.values),
            "base_values": _encode(value.base_values),
            "data": _encode(value.data),
            "feature_names": _encode(value.feature_names),
            "output_names": _encode(value.output_names),
        }
    if isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        f"Unsupported audit-session value type: {type(value).__name__}."
    )


def _decode(value):
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if not isinstance(value, dict):
        return value

    value_type = value.get("__xaida_type__")
    if value_type == "dict":
        return {
            _decode(key): _decode(item)
            for key, item in value["items"]
        }
    if value_type == "tuple":
        return tuple(_decode(item) for item in value["items"])
    if value_type == "set":
        return set(_decode(item) for item in value["items"])
    if value_type == "dataframe":
        dataframe = pd.DataFrame(
            _decode(value["data"]),
            columns=_decode_index(value["columns"]),
            index=_decode_index(value["index"]),
        )
        for position, dtype in enumerate(value["dtypes"]):
            try:
                dataframe.isetitem(
                    position,
                    dataframe.iloc[:, position].astype(dtype),
                )
            except (TypeError, ValueError) as error:
                raise SessionPersistenceError(
                    f"Unsupported saved dataframe dtype: {dtype}."
                ) from error
        return dataframe
    if value_type == "series":
        series = pd.Series(
            _decode(value["data"]),
            index=_decode_index(value["index"]),
            name=_decode(value["name"]),
        )
        try:
            return series.astype(value["dtype"])
        except (TypeError, ValueError) as error:
            raise SessionPersistenceError(
                f"Unsupported saved series dtype: {value['dtype']}."
            ) from error
    if value_type == "ndarray":
        return np.asarray(
            _decode(value["data"]),
            dtype=np.dtype(value["dtype"]),
        ).reshape(value["shape"])
    if value_type in {"datetime", "Timestamp", "date", "time"}:
        constructors = {
            "datetime": datetime.fromisoformat,
            "Timestamp": datetime.fromisoformat,
            "date": date.fromisoformat,
            "time": time.fromisoformat,
        }
        return constructors[value_type](value["value"])
    if value_type == "shap_explanation":
        import shap

        return shap.Explanation(
            values=_decode(value["values"]),
            base_values=_decode(value["base_values"]),
            data=_decode(value["data"]),
            feature_names=_decode(value["feature_names"]),
            output_names=_decode(value["output_names"]),
        )
    return {
        key: _decode(item)
        for key, item in value.items()
    }


def _serialize_session(session):
    state = session.__dict__.copy()
    try:
        encoded_state = _encode(state)
    except TypeError as error:
        raise SessionPersistenceError(str(error)) from error
    document = {
        "format_version": SNAPSHOT_FORMAT_VERSION,
        "session": encoded_state,
    }
    serialized = json.dumps(
        document,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(serialized) > MAX_UNCOMPRESSED_SNAPSHOT_BYTES:
        raise SessionPersistenceError(
            "The audit snapshot exceeds the uncompressed storage size limit."
        )
    return gzip.compress(serialized)


def _deserialize_session(contents, expected_session_id):
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(contents)) as snapshot:
            serialized = snapshot.read(
                MAX_UNCOMPRESSED_SNAPSHOT_BYTES + 1
            )
        if len(serialized) > MAX_UNCOMPRESSED_SNAPSHOT_BYTES:
            raise SessionPersistenceError(
                "The saved audit snapshot exceeds the supported size limit."
            )
        document = json.loads(serialized)
    except SessionPersistenceError:
        raise
    except (OSError, EOFError, json.JSONDecodeError) as error:
        raise SessionPersistenceError(
            "The saved audit snapshot is damaged or unreadable."
        ) from error
    if (
        not isinstance(document, dict)
        or document.get("format_version") != SNAPSHOT_FORMAT_VERSION
    ):
        raise SessionPersistenceError(
            "The saved audit snapshot uses an unsupported format version."
        )

    state = _decode(document.get("session"))
    if not isinstance(state, dict):
        raise SessionPersistenceError(
            "The saved audit snapshot has an invalid structure."
        )
    session = AuditSession()
    session.__dict__.update(state)
    metadata = getattr(session, "metadata", None)
    if (
        not isinstance(metadata, dict)
        or metadata.get("session_id") != expected_session_id
    ):
        raise SessionPersistenceError(
            "The saved audit snapshot does not match its session record."
        )
    return session


def _ensure_schema(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS xaida_audit_sessions (
            session_id TEXT PRIMARY KEY,
            owner_hash TEXT NOT NULL,
            object_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS xaida_audit_sessions_expiry_idx
        ON xaida_audit_sessions (expires_at)
        """
    )


def _validate_session_id(session_id):
    try:
        return str(uuid.UUID(str(session_id)))
    except (ValueError, TypeError, AttributeError) as error:
        raise SessionUnavailableError(
            "The audit session link is invalid."
        ) from error


def save_audit_session(session, owner_email):
    session_id = _validate_session_id(
        session.metadata.get("session_id")
    )
    owner_hash = _owner_hash(owner_email)
    object_name = _session_object_name(session_id)
    contents = _serialize_session(session)
    if len(contents) > MAX_SNAPSHOT_BYTES:
        raise SessionPersistenceError(
            "The audit snapshot exceeds the configured storage size limit."
        )

    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    expires_at = (now + timedelta(hours=_retention_hours())).isoformat()
    marker = parameter_placeholder()
    try:
        with connect_database() as connection:
            _ensure_schema(connection)
            existing = connection.execute(
                "SELECT owner_hash, created_at FROM xaida_audit_sessions "
                f"WHERE session_id = {marker}",
                (session_id,),
            ).fetchone()
            if existing and existing[0] != owner_hash:
                raise SessionUnavailableError(
                    "This audit session is unavailable to the signed-in user."
                )
            created_at = existing[1] if existing else timestamp
            upload_bytes(
                object_name,
                contents,
                "application/gzip",
            )
            cursor = connection.execute(
                f"""
                INSERT INTO xaida_audit_sessions (
                    session_id,
                    owner_hash,
                    object_name,
                    created_at,
                    updated_at,
                    expires_at
                ) VALUES ({marker}, {marker}, {marker}, {marker}, {marker}, {marker})
                ON CONFLICT (session_id) DO UPDATE SET
                    object_name = excluded.object_name,
                    updated_at = excluded.updated_at,
                    expires_at = excluded.expires_at
                WHERE xaida_audit_sessions.owner_hash = excluded.owner_hash
                """,
                (
                    session_id,
                    owner_hash,
                    object_name,
                    created_at,
                    timestamp,
                    expires_at,
                ),
            )
            if cursor.rowcount != 1:
                raise SessionUnavailableError(
                    "This audit session is unavailable to the signed-in user."
                )
    except SessionPersistenceError:
        raise
    except Exception as error:
        raise SessionPersistenceError(
            "XAIDA could not durably save the audit session. Do not close or "
            "refresh the application until storage connectivity is restored."
        ) from error


def load_audit_session(session_id, owner_email):
    session_id = _validate_session_id(session_id)
    owner_hash = _owner_hash(owner_email)
    marker = parameter_placeholder()
    try:
        with connect_database() as connection:
            _ensure_schema(connection)
            row = connection.execute(
                "SELECT owner_hash, object_name, expires_at "
                "FROM xaida_audit_sessions "
                f"WHERE session_id = {marker}",
                (session_id,),
            ).fetchone()
        if row is None or row[0] != owner_hash:
            raise SessionUnavailableError(
                "This audit session is unavailable to the signed-in user."
            )

        expires_at = datetime.fromisoformat(row[2])
        if expires_at <= datetime.now(timezone.utc):
            delete_audit_session(session_id, owner_email)
            retention_hours = _retention_hours()
            raise SessionExpiredError(
                "This audit session expired after "
                f"{retention_hours} hours of inactivity. "
                "Start a new analysis to continue."
            )

        contents = download_bytes(row[1])
        if contents is None:
            raise SessionExpiredError(
                "The saved audit snapshot has expired or is no longer "
                "available. Start a new analysis to continue."
            )
        return _deserialize_session(contents, session_id)
    except SessionPersistenceError:
        raise
    except Exception as error:
        raise SessionPersistenceError(
            "XAIDA could not load the saved audit session."
        ) from error


def delete_audit_session(session_id, owner_email):
    session_id = _validate_session_id(session_id)
    owner_hash = _owner_hash(owner_email)
    marker = parameter_placeholder()
    try:
        with connect_database() as connection:
            _ensure_schema(connection)
            row = connection.execute(
                "SELECT owner_hash FROM xaida_audit_sessions "
                f"WHERE session_id = {marker}",
                (session_id,),
            ).fetchone()
            if row is None:
                return False
            if row[0] != owner_hash:
                raise SessionUnavailableError(
                    "This audit session is unavailable to the signed-in user."
                )
            delete_prefix(_object_prefix(session_id))
            connection.execute(
                "DELETE FROM xaida_audit_sessions "
                f"WHERE session_id = {marker} AND owner_hash = {marker}",
                (session_id, owner_hash),
            )
        return True
    except SessionPersistenceError:
        raise
    except Exception as error:
        raise SessionPersistenceError(
            "XAIDA could not delete the saved audit data. The audit was not "
            "reset; contact the application administrator."
        ) from error


def delete_expired_sessions():
    deleted = 0
    marker = parameter_placeholder()
    now = datetime.now(timezone.utc).isoformat()
    try:
        with connect_database() as connection:
            _ensure_schema(connection)
            expired = connection.execute(
                "SELECT session_id FROM xaida_audit_sessions "
                f"WHERE expires_at <= {marker}",
                (now,),
            ).fetchall()
            for (session_id,) in expired:
                delete_prefix(_object_prefix(session_id))
                connection.execute(
                    "DELETE FROM xaida_audit_sessions "
                    f"WHERE session_id = {marker}",
                    (session_id,),
                )
                deleted += 1
    except Exception as error:
        raise SessionPersistenceError(
            "XAIDA could not clean up expired audit sessions."
        ) from error
    return deleted


def _query_session_id():
    value = st.query_params.get(SESSION_QUERY_PARAM)
    return value if isinstance(value, str) and value else None


def _set_query_session_id(session_id):
    st.query_params[SESSION_QUERY_PARAM] = session_id


def _clear_query_session_id():
    st.query_params.pop(SESSION_QUERY_PARAM, None)


def get_or_create_session(create_session):
    current = st.session_state.get("audit_session")
    requested_id = _query_session_id()

    if not session_storage_enabled():
        if current is None:
            current = create_session()
            st.session_state["audit_session"] = current
        return current

    owner_email = _authenticated_owner()
    owner_hash = _owner_hash(owner_email)
    if (
        current is not None
        and requested_id == current.metadata.get("session_id")
        and st.session_state.get("xaida_session_owner_hash") == owner_hash
    ):
        return current

    if requested_id:
        current = load_audit_session(requested_id, owner_email)
    else:
        current = create_session()
        _set_query_session_id(current.metadata["session_id"])
        save_audit_session(current, owner_email)

    st.session_state["audit_session"] = current
    st.session_state["xaida_session_owner_hash"] = owner_hash
    return current


def save_active_session(session):
    if session_storage_enabled():
        save_audit_session(session, _authenticated_owner())


def authenticated_owner_hash():
    return _owner_hash(_authenticated_owner())


def delete_active_session(session):
    if session_storage_enabled():
        delete_audit_session(
            session.metadata["session_id"],
            _authenticated_owner(),
        )


def clear_session_link():
    _clear_query_session_id()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cleanup-expired",
        action="store_true",
        help="Delete expired audit snapshots and their Cloud SQL metadata.",
    )
    args = parser.parse_args()
    if not args.cleanup_expired:
        parser.error("Use --cleanup-expired to run the retention cleanup.")
    if not session_storage_enabled():
        parser.error(
            "Set XAIDA_SESSION_STORAGE_BACKEND=gcs before running cleanup."
        )
    print(f"Deleted {delete_expired_sessions()} expired audit sessions.")


if __name__ == "__main__":
    main()
