from audit.services.audit_readiness import (
    calculate_audit_readiness,
)

def build_audit_readiness_context(
    session,
):

    readiness = (
        calculate_audit_readiness(
            session
        )
    )

    return {

        "audit_readiness_score":
        readiness.get(
            "score",
            0,
        ),

        "audit_readiness_status":
        readiness.get(
            "status",
            "Not Ready",
        ),

        "audit_ready":
        readiness.get(
            "audit_ready",
            False,
        ),

        "audit_readiness_breakdown":
        readiness.get(
            "breakdown",
            [],
        ),

        "audit_readiness_deductions":
        readiness.get(
            "deductions",
            [],
        ),

        "explainability_coverage":
        readiness.get(
            "explainability_coverage",
            0,
        ),

        "explained_records":
        readiness.get(
            "explained_records",
            0,
        ),

        "flagged_records":
        readiness.get(
            "flagged_records",
            0,
        ),
    }