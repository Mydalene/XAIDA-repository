# ============================================================
# DATASET VERSION MANAGER
# ============================================================

from audit.change_tracker import (
    log_dataset_change,
)


def get_current_version(
    session,
):
    return session.analysis.get(
        "dataset_version",
        0,
    )


def get_dataset_versions(
    session,
):

    return session.analysis.setdefault(
        "dataset_versions",
        {},
    )


def get_version_metadata(
    session,
):
    return session.analysis.setdefault(
        "dataset_version_metadata",
        {},
    )


def create_dataset_version(
    session,
    dataframe,
    stage,
    action,
    metadata=None,
):

    current_version = (
        get_current_version(session)
    )

    new_version = (
        current_version + 1
    )

    session.analysis[
        "dataset_version"
    ] = new_version

    versions = (
        get_dataset_versions(session)
    )

    versions[
        new_version
    ] = (
        dataframe.copy()
        if dataframe is not None
        else None
    )

    version_metadata = (
        get_version_metadata(session)
    )

    metadata = metadata or {}
    version_metadata[
        new_version
    ] = {
        "stage": stage,
        "action": action,
        **metadata,
    }

    change_details = f"Dataset version V{new_version} created"
    detail_labels = {
        "records_removed": "records removed",
        "imputation_count": "imputation rules applied",
        "explanations_added": "explanations added",
        "total_findings": "findings generated",
        "findings_count": "findings included",
    }
    metadata_details = [
        f"{label}: {metadata[key]}"
        for key, label in detail_labels.items()
        if metadata.get(key) is not None
    ]
    if metadata_details:
        change_details += "; " + "; ".join(metadata_details)

    log_dataset_change(
        session=session,
        stage=stage,
        action=action,
        details=change_details,
        version=new_version,
    )

    return new_version

def get_dataset_version(
    session,
    version,
):
    versions = (
        get_dataset_versions(
            session
        )
    )

    return versions.get(
        version
    )

def register_dataset_version(
    session,
    version,
    dataframe,
):
    versions = (
        get_dataset_versions(
            session
        )
    )

    versions[
        version
    ] = (
        dataframe.copy()
        if dataframe is not None
        else None
    )

def get_latest_dataset(
    session,
):
    current_version = (
        get_current_version(
            session
        )
    )

    return get_dataset_version(
        session,
        current_version,
    )

def get_version_info(
    session,
    version,
):
    metadata = (
        get_version_metadata(
            session
        )
    )

    return metadata.get(
        version,
        {},
    )