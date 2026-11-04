# ============================================================
# XAIDA 5.0
# assistant/session_validator.py
# ============================================================

VALID_WORKFLOW_STAGES = {
    "initialization",
    "dataset",
    "data_preparation",
    "duplicate_review",
    "analysis",
    "explainability",
    "audit_review",
    "findings",
    "reporting",
    "audit_completion",
    "closed",
}


def validate_session(session):
    """
    Validate session health before
    building context or generating
    responses.
    """

    errors = []

    # ===================================
    # METADATA
    # ===================================

    if not hasattr(session, "metadata"):
        errors.append(
            "Session metadata is missing."
        )
    else:

        workflow_stage = (
            session.metadata.get(
                "workflow_stage"
            )
        )

        if not workflow_stage:

            errors.append(
                "Workflow stage is missing."
            )

        elif (
            workflow_stage
            not in VALID_WORKFLOW_STAGES
        ):
            errors.append(
                (
                    f"Invalid workflow stage: "
                    f"{workflow_stage}"
                )
            )

    # ===================================
    # DATASET
    # ===================================

    if not hasattr(session, "dataset"):
        errors.append(
            "Dataset container is missing."
        )

    # ===================================
    # DUPLICATES
    # ===================================

    if not hasattr(session, "duplicates"):
        errors.append(
            "Duplicate review container is missing."
        )

    # ===================================
    # ANALYSIS
    # ===================================

    if not hasattr(session, "analysis"):
        errors.append(
            "Analysis container is missing."
        )

    # ===================================
    # FINDINGS
    # ===================================

    if not hasattr(session, "findings"):
        errors.append(
            "Findings container is missing."
        )

    else:

        if not isinstance(
            session.findings,
            dict,
        ):
            errors.append(
                "Findings container is invalid."
            )

    # ===================================
    # EXPLAINABILITY
    # ===================================

    if not hasattr(
        session,
        "explainability",
    ):
        errors.append(
            "Explainability container is missing."
        )

    # ===================================
    # AUDIT LOG
    # ===================================

    if not hasattr(
        session,
        "audit_log",
    ):
        errors.append(
            "Audit log is missing."
        )

    # ===================================
    # RESULT
    # ===================================

    if errors:

        return (
            False,
            errors,
        )

    return (
        True,
        [],
    )