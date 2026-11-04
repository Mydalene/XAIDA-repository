import os


def cloud_storage_enabled():
    backend = os.getenv(
        "XAIDA_SESSION_STORAGE_BACKEND",
        "local",
    ).strip().casefold()
    if backend not in {"local", "gcs"}:
        raise RuntimeError(
            "XAIDA_SESSION_STORAGE_BACKEND must be 'local' or 'gcs'."
        )
    return backend == "gcs"


def _bucket():
    bucket_name = os.getenv("XAIDA_SESSION_STORAGE_BUCKET", "").strip()
    if not bucket_name:
        raise RuntimeError(
            "XAIDA_SESSION_STORAGE_BUCKET must name the private session "
            "storage bucket."
        )

    try:
        from google.cloud import storage
    except ImportError as error:
        raise RuntimeError(
            "Google Cloud Storage support is missing. Install the project "
            "requirements."
        ) from error

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "").strip() or None
    return storage.Client(project=project).bucket(bucket_name)


def upload_bytes(object_name, contents, content_type):
    blob = _bucket().blob(object_name)
    blob.upload_from_string(contents, content_type=content_type)
    return blob.generation


def download_bytes(object_name):
    from google.api_core.exceptions import NotFound

    blob = _bucket().blob(object_name)
    try:
        return blob.download_as_bytes()
    except NotFound:
        return None


def delete_prefix(prefix):
    bucket = _bucket()
    for blob in bucket.list_blobs(prefix=prefix, versions=True):
        blob.delete(if_generation_match=blob.generation)
