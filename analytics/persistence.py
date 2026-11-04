# ============================================================
# XAIDA PERSISTENCE
# Atomic Save + Integrity Hash
# ============================================================

import hashlib
import io
import json
import os
import tempfile
from pathlib import Path

import joblib

from core.cloud_storage import (
    cloud_storage_enabled,
    download_bytes,
    upload_bytes,
)

ANALYSIS_DIR = Path(
    "analysis_artifacts"
)

ANALYSIS_DIR.mkdir(
    exist_ok=True,
)

# ============================================================
# HASHING
# ============================================================

def compute_sha256(
    filepath,
):

    sha256 = hashlib.sha256()

    with open(
        filepath,
        "rb",
    ) as file:

        for chunk in iter(
            lambda: file.read(8192),
            b"",
        ):

            sha256.update(
                chunk
            )

    return sha256.hexdigest()


# ============================================================
# ATOMIC SAVE
# ============================================================

def atomic_joblib_dump(
    obj,
    filepath,
):

    filepath = Path(
        filepath
    )

    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=filepath.parent,
        suffix=".tmp",
    ) as tmp:

        temp_path = Path(
            tmp.name
        )

    try:

        joblib.dump(
            obj,
            temp_path,
        )

        os.replace(
            temp_path,
            filepath,
        )

    finally:

        if temp_path.exists():

            temp_path.unlink(
                missing_ok=True
            )


# ============================================================
# SAVE ANALYSIS ARTIFACT
# ============================================================

def save_analysis_artifact(
    analysis_result,
    dataset_version,
    session_id=None,
):
    if cloud_storage_enabled():
        if not session_id:
            raise ValueError(
                "A session ID is required to store analysis artifacts."
            )
        import uuid

        session_id = str(uuid.UUID(str(session_id)))
        output = io.BytesIO()
        joblib.dump(analysis_result, output)
        artifact_contents = output.getvalue()
        sha256_hash = hashlib.sha256(artifact_contents).hexdigest()
        prefix = f"audit-sessions/{session_id}/analysis/"
        artifact_name = f"analysis_v{dataset_version}.joblib"
        metadata_name = f"analysis_v{dataset_version}.json"
        metadata = {
            "dataset_version": dataset_version,
            "artifact_file": artifact_name,
            "sha256": sha256_hash,
        }
        upload_bytes(
            prefix + artifact_name,
            artifact_contents,
            "application/octet-stream",
        )
        upload_bytes(
            prefix + metadata_name,
            json.dumps(metadata, indent=4).encode("utf-8"),
            "application/json",
        )
        bucket_name = os.getenv("XAIDA_SESSION_STORAGE_BUCKET", "").strip()
        return {
            "artifact": f"gs://{bucket_name}/{prefix}{artifact_name}",
            "metadata": f"gs://{bucket_name}/{prefix}{metadata_name}",
            "sha256": sha256_hash,
        }

    artifact_path = (
        ANALYSIS_DIR
        /
        f"analysis_v{dataset_version}.joblib"
    )

    atomic_joblib_dump(
        analysis_result,
        artifact_path,
    )

    sha256_hash = (
        compute_sha256(
            artifact_path
        )
    )

    metadata = {

        "dataset_version":
            dataset_version,

        "artifact_file":
            artifact_path.name,

        "sha256":
            sha256_hash,
    }

    metadata_path = (
        ANALYSIS_DIR
        /
        f"analysis_v{dataset_version}.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    return {

        "artifact":
            str(
                artifact_path
            ),

        "metadata":
            str(
                metadata_path
            ),

        "sha256":
            sha256_hash,
    }


# ============================================================
# LOAD ANALYSIS ARTIFACT
# ============================================================

def load_analysis_artifact(
    dataset_version,
    session_id=None,
):
    if cloud_storage_enabled():
        if not session_id:
            raise ValueError(
                "A session ID is required to load analysis artifacts."
            )
        import uuid

        session_id = str(uuid.UUID(str(session_id)))
        prefix = f"audit-sessions/{session_id}/analysis/"
        metadata_contents = download_bytes(
            f"{prefix}analysis_v{dataset_version}.json"
        )
        artifact_contents = download_bytes(
            f"{prefix}analysis_v{dataset_version}.joblib"
        )
        if metadata_contents is None or artifact_contents is None:
            raise FileNotFoundError(
                "The stored analysis artifact was not found."
            )
        metadata = json.loads(metadata_contents)
        current_hash = hashlib.sha256(artifact_contents).hexdigest()
        if current_hash != metadata["sha256"]:
            raise ValueError("Artifact integrity check failed.")
        return joblib.load(io.BytesIO(artifact_contents))

    artifact_path = (
        ANALYSIS_DIR
        /
        f"analysis_v{dataset_version}.joblib"
    )

    metadata_path = (
        ANALYSIS_DIR
        /
        f"analysis_v{dataset_version}.json"
    )

    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as file:

        metadata = json.load(
            file
        )

    current_hash = (
        compute_sha256(
            artifact_path
        )
    )

    if (
        current_hash
        !=
        metadata["sha256"]
    ):

        raise ValueError(
            "Artifact integrity check failed."
        )

    return joblib.load(
        artifact_path
    )