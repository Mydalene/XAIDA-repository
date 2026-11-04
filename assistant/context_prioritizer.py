# ============================================================
# XAIDA 5.2
# assistant/context_prioritizer.py
# ============================================================

from assistant.stage_registry import (
    STAGE_REGISTRY,
)

CORE_FIELDS = [
    "workflow_stage",

    # Workflow
    "next_recommended_step",

    # Audit
    "audit_name",

    # Dataset
    "dataset_name",
    "rows",
    "columns",
    "column_names",
    "dataset_version",

    # Audit Readiness
    "audit_readiness_score",
    "audit_readiness_status",
    "audit_ready",
    "audit_readiness_breakdown",

    # Risk
    "risk_level",
    "flagged_transactions",

    # Findings
    "validated_findings",
    "open_findings",
]


# ============================================================
# PRIORITISED CONTEXT
# ============================================================

def build_prioritized_context(
    full_context,
    categories,
):
    """
    Keep all audit evidence.

    Prioritise relevant evidence
    without removing supporting
    evidence.
    """

    if isinstance(
        categories,
        str,
    ):
        categories = [categories]

    primary_evidence = {}
    secondary_evidence = {}

    # ------------------------------------------------
    # Core Context
    # ------------------------------------------------

    for field in CORE_FIELDS:

        if field in full_context:

            primary_evidence[field] = (
                full_context[field]
            )

    # ------------------------------------------------
    # Stage Context
    # ------------------------------------------------

    for category in categories:

        fields = (
            STAGE_REGISTRY
            .get(category, {})
            .get("fields", [])
        )

        for field in fields:

            if field in full_context:

                primary_evidence[field] = (
                    full_context[field]
                )

    # ------------------------------------------------
    # Remaining Evidence
    # ------------------------------------------------

    for key, value in (
        full_context.items()
    ):

        if key not in primary_evidence:

            secondary_evidence[key] = value

    return {
        "primary_evidence":
            primary_evidence,

        "secondary_evidence":
            secondary_evidence,

        "context_summary": {
            "categories": categories,

            "primary_count":
                len(primary_evidence),

            "secondary_count":
                len(secondary_evidence),
        },
    }

    sorted(
        aliases,
        key=len,
        reverse=True,
    )