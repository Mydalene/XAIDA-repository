
from datetime import (
    datetime,
    UTC,
)

# ============================================================
# DATASET CHANGE TRACKER
# ============================================================

def get_change_log(
    session,
):
    """
    Returns the dataset change history.
    """

    return session.analysis.setdefault(
        "dataset_change_log",
        [],
    )


def log_dataset_change(
    session,
    stage,
    action,
    details,
    version=None,
):
    """
    Records a dataset change event.
    """

    changes = (
        get_change_log(
            session
        )
    )

    changes.append(
        {
            "timestamp":
                datetime.now(
                    UTC
                ).isoformat(),

            "version":
                version,

            "stage":
                stage,

            "action":
                action,

            "details":
                details,
        }
    )


def get_changes_for_version(
    session,
    version,
):
    """
    Returns all changes associated
    with a dataset version.
    """

    return [
        change
        for change in get_change_log(
            session
        )
        if change.get(
            "version"
        ) == version
    ]


def clear_change_log(
    session,
):
    """
    Clears dataset history.
    """

    session.analysis[
        "dataset_change_log"
    ] = []