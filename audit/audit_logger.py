from datetime import datetime

def log_audit_event(
    session,
    stage,
    action,
    details,
):

    session.audit_log.append(

        {
            "timestamp":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "dataset_version":
                session.analysis.get(
                    "dataset_version",
                    0,
                ),

            "stage":
                stage,

            "action":
                action,

            "details":
                details,
        }

    )

def normalise_audit_log(
    session,
):

    if not hasattr(
        session,
        "audit_log",
    ):
        return

    cleaned = []

    for item in session.audit_log:

        if (
            not isinstance(
                item,
                dict,
            )
        ):
            continue

        item.setdefault(
            "dataset_version",
            0,
        )

        cleaned.append(
            item
        )

    session.audit_log = cleaned