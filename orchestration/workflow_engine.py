# ============================================================
# XAIDA 4.0
# orchestration/workflow_engine.py
# ============================================================

import pandas as pd


# ============================================================
# WORKFLOW STAGES
# ============================================================

INITIALIZATION = "initialization"
DATASET = "dataset"
DATA_PREPARATION = "data_preparation"
DUPLICATE_REVIEW = "duplicate_review"
ANALYSIS = "analysis"
EXPLAINABILITY = "explainability"
AUDIT_REVIEW = "audit_review"
FINDINGS = "findings"
REPORTING = "reporting"
AUDIT_COMPLETION = "audit_completion"
CLOSED = AUDIT_COMPLETION


# ============================================================
# VALID TRANSITIONS
# ============================================================

WORKFLOW_TRANSITIONS = {

    INITIALIZATION: [
        DATASET,
    ],

    DATASET: [
        DATA_PREPARATION,
    ],

    DATA_PREPARATION: [
        DUPLICATE_REVIEW,
        ANALYSIS,
    ],

    DUPLICATE_REVIEW: [
        ANALYSIS,
    ],

    ANALYSIS: [
        EXPLAINABILITY,
    ],

    EXPLAINABILITY: [
        AUDIT_REVIEW,
    ],

    AUDIT_REVIEW: [
        FINDINGS,
    ],

    FINDINGS: [
        REPORTING,
    ],

    REPORTING: [
        AUDIT_COMPLETION,
    ],

    AUDIT_COMPLETION: [],
}

# ============================================================
# CURRENT STAGE
# ============================================================

def get_current_stage(session):

    return session.metadata.get(
        "workflow_stage",
        DATASET,
    )


# ============================================================
# VALIDATE TRANSITION
# ============================================================

def can_transition(
    session,
    next_stage,
):

    current_stage = (
        get_current_stage(
            session
        )
    )

    allowed = (
        WORKFLOW_TRANSITIONS.get(
            current_stage,
            [],
        )
    )

    return (
        next_stage in allowed
    )

# ============================================================
# SET STAGE
# ============================================================

def transition_to(
    session,
    next_stage,
):

    current_stage = get_current_stage(session)
    if current_stage == next_stage:
        return session

    if not can_transition(
        session,
        next_stage,
    ):
        raise ValueError(
            f"Invalid workflow transition: "
            f"{get_current_stage(session)} "
            f"-> "
            f"{next_stage}"
        )

    session.metadata[
        "workflow_stage"
    ] = next_stage

    return session

# ============================================================
# DUPLICATES REQUIRED
# ============================================================

def duplicate_review_required(
    session,
):

    return (
        session.duplicates.get(
            "duplicate_count",
            0,
        ) > 0
    )


# ============================================================
# ANALYSIS ALLOWED
# ============================================================

def can_run_analysis(
    session,
):

    current_stage = (
        get_current_stage(
            session
        )
    )

    if current_stage == next_stage:
        return session

    return (
        current_stage
        == ANALYSIS
    )

# ============================================================
# PROCESS BUTTON GUARDS
# ============================================================

def can_open_explainability(
    session,
):

    return (
        get_current_stage(session)
        == ANALYSIS
        and
        session.analysis.get(
            "analysis_complete",
            False,
        )
    )


def can_open_audit_review(
    session,
):

    return (
        get_current_stage(session)
        == EXPLAINABILITY
    )


def can_show_findings(
    session,
):

    return (
        get_current_stage(session)
        == AUDIT_REVIEW
    )


def can_generate_report(
    session,
):

    return (
        get_current_stage(session)
        == FINDINGS
    )

# ============================================================
# NEXT RECOMMENDED STEP
# ============================================================

def get_next_recommended_step(
    session,
):

    current_stage = (
        get_current_stage(
            session
        )
    )

    if current_stage == DATASET:
        return "Process Data Preparation"

    if current_stage == INITIALIZATION:
        return "Load or select a dataset"

    if current_stage == DATA_PREPARATION:

        if (
            session.duplicates.get(
                "duplicate_count",
                0,
            ) > 0
        ):
            return (
                "Proceed To Duplicate Review"
            )

        return (
            "Proceed To Analysis"
        )

    if current_stage == DUPLICATE_REVIEW:

        if not session.duplicates.get(
            "duplicate_review_complete",
            False,
        ):
            return (
                "Complete Duplicate Review"
            )

        return (
            "Proceed To Analysis"
        )

    if current_stage == ANALYSIS:

        if not session.analysis.get(
            "analysis_complete",
            False,
        ):
            return (
                "Run Analysis"
            )

        return (
            "Open Explainability"
        )

    if current_stage == EXPLAINABILITY:

        return (
            "Open Audit Review"
        )

    if current_stage == AUDIT_REVIEW:

        if session.review.get("audit_review_complete", False):
            return "Proceed To Findings"

        review_records = session.review.get("records")
        if (
            not isinstance(review_records, pd.DataFrame)
            or "Anomaly Flag" not in review_records.columns
            or "Auditor Assessment" not in review_records.columns
        ):
            return "Review flagged records"

        remaining_reviews = (
            review_records["Anomaly Flag"].fillna(False).astype(bool)
            & review_records["Auditor Assessment"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
        ).sum()

        if remaining_reviews > 0:
            return "Review flagged records"

        return "Save Review Decisions"

    if current_stage == FINDINGS:

        return (
            "Generate Report"
        )

    if current_stage == REPORTING:

        return "Complete Audit"

    if current_stage == AUDIT_COMPLETION:
        return "Audit Complete"

    return "Workflow Complete"
