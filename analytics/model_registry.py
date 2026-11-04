# ============================================================
# XAIDA MODEL REGISTRY
# ============================================================

from io import BytesIO
from pathlib import Path
import os
import uuid

import joblib

from core.cloud_storage import (
    cloud_storage_enabled,
    download_bytes,
    upload_bytes,
)

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(
    exist_ok=True,
)

# ============================================================
# SAVE
# ============================================================

def save_model(
    model,
    model_name,
    session_id=None,
):
    if cloud_storage_enabled():
        if not session_id:
            raise ValueError(
                "A session ID is required to store a model in Cloud Storage."
            )
        session_id = str(uuid.UUID(str(session_id)))
        output = BytesIO()
        joblib.dump(model, output)
        object_name = (
            f"audit-sessions/{session_id}/models/{model_name}.joblib"
        )
        upload_bytes(
            object_name,
            output.getvalue(),
            "application/octet-stream",
        )
        bucket_name = os.getenv("XAIDA_SESSION_STORAGE_BUCKET", "").strip()
        return f"gs://{bucket_name}/{object_name}"

    filepath = (
        MODEL_DIR
        / f"{model_name}.joblib"
    )

    joblib.dump(
        model,
        filepath,
    )

    return str(filepath)


# ============================================================
# LOAD
# ============================================================

def load_model(
    model_name,
    session_id=None,
):
    if cloud_storage_enabled():
        if not session_id:
            raise ValueError(
                "A session ID is required to load a model from Cloud Storage."
            )
        session_id = str(uuid.UUID(str(session_id)))
        object_name = (
            f"audit-sessions/{session_id}/models/{model_name}.joblib"
        )
        contents = download_bytes(object_name)
        if contents is None:
            raise FileNotFoundError("The stored model was not found.")
        return joblib.load(BytesIO(contents))

    filepath = (
        MODEL_DIR
        / f"{model_name}.joblib"
    )

    return joblib.load(
        filepath
    )