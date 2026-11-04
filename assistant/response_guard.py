# ============================================================
# XAIDA 5.0
# assistant/response_guard.py
# ============================================================

def verify_context(
    category,
    context,
):
    warnings = []

    critical_fields = [
        "dataset_name",
        "workflow_stage",
    ]

    for field in critical_fields:

        if not context.get(field):

            warnings.append(
                f"Missing: {field}"
            )

    return (
        True,
        warnings,
    )