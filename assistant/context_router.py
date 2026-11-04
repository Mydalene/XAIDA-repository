# ============================================================
# XAIDA 5.0
# assistant/context_router.py
# ============================================================
from assistant.stage_registry import (
    STAGE_REGISTRY,
)


def classify_question(
    user_message,
):
    text = (
        user_message
        .lower()
        .strip()
    )

    matching_aliases = []
    for (
        stage,
        config,
    ) in STAGE_REGISTRY.items():

        aliases = (
            config
            .get(
                "aliases",
                [],
            )
        )

        matching_aliases.extend(
            (len(alias), stage)
            for alias in aliases
            if alias in text
        )

    if matching_aliases:
        return max(matching_aliases)[1]

    return "general"

def build_focused_context(
    full_context,
    category,
):
    """
    Keep critical audit context
    while prioritising context
    relevant to the user's question.
    """

    core = {
        "workflow_stage":
            full_context.get(
                "workflow_stage"
            ),

        "audit_name":
            full_context.get(
                "audit_name"
            ),

        "dataset_name":
            full_context.get(
                "dataset_name"
            ),

        "feature_count":
            full_context.get(
                "feature_count"
            ),

        "rows":
            full_context.get(
                "rows"
            ),

        "risk_level":
            full_context.get(
                "risk_level"
            ),

        "flagged_transactions":
            full_context.get(
                "flagged_transactions"
            ),

        "validated_findings":
            full_context.get(
                "validated_findings"
            ),

        "open_findings":
            full_context.get(
                "open_findings"
            ),
    }

    result = dict(core)

    fields = (
        STAGE_REGISTRY
        .get(category, {})
        .get("fields", [])
    )

    for field in fields:

        result[field] = (
            full_context.get(field)
        )

    return result