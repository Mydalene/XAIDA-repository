# ============================================================
# assistant/context_builder.py
# ============================================================


# ------------------------------------------------------------
# WORKFLOW STAGE CONTEXTS
# ------------------------------------------------------------

from assistant.context.dataset_context import (
    build_dataset_context,
)

from assistant.context.data_preparation_context import (
    build_data_preparation_context,
)

from assistant.context.duplicate_review_context import (
    build_duplicate_review_context,
)

from assistant.context.analysis_context import (
    build_analysis_context,
)

from assistant.context.explainability_context import (
    build_explainability_context,
)

from assistant.context.audit_review_context import (
    build_audit_review_context,
)

from assistant.context.findings_context import (
    build_findings_context,
)

from assistant.context.reporting_context import (
    build_reporting_context,
)

# ------------------------------------------------------------
# EVIDENCE CONTEXTS
# ------------------------------------------------------------

from assistant.context.lineage_context import (
    build_lineage_context,
)

from assistant.context.audit_trail_context import (
    build_trail_context,
)

from assistant.context.traceability_context import (
    build_traceability_context,
)

# ------------------------------------------------------------
# GLOBAL CONTEXTS
# ------------------------------------------------------------

from assistant.context.global_context import (
    build_global_context,
)

from assistant.context.audit_readiness_context import (
    build_audit_readiness_context,
)

# ------------------------------------------------------------
# GLOBAL CAPABILITIES
# ------------------------------------------------------------

from assistant.context.methodology_context import (
    build_methodology_context,
)

from assistant.context.narrative_context import (
    build_narrative_context,
)

from assistant.context.platform_help_context import (
    build_platform_help_context,
)

# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(
    session,
    user_message=None,
):

    results = (
        session.analysis.get(
            "results",
            {},
        )
    )

    risk_summary = (
        results.get(
            "risk_summary",
            {},
        )
    )

    top_features = (
        results.get(
            "top_features"
        )
    )

    context = {}

    # ========================================================
    # GLOBAL CONTEXTS
    # ========================================================

    context.update(
        build_global_context(
            session
        )
    )

    context.update(
        build_audit_readiness_context(
            session
        )
    )

    # ========================================================
    # WORKFLOW STAGE CONTEXTS
    # ========================================================

    context.update(
        build_dataset_context(
            session
        )
    )

    context.update(
        build_data_preparation_context(
            session,
            include_record_identifiers=(
                user_message is not None
                and any(
                    term in user_message.lower()
                    for term in (
                        "record id",
                        "record identifier",
                        "which records",
                        "affected records",
                        "complete list of identifiers",
                        "list the ids",
                        "ids of",
                        "individual record",
                    )
                )
            ),
        )
    )

    context.update(
        build_duplicate_review_context(
            session
        )
    )

    context.update(
        build_analysis_context(
            session,
            risk_summary,
        )
    )

    context.update(
        build_explainability_context(
            session,
            top_features,
        )
    )

    context.update(
        build_audit_review_context(
            session,
            risk_summary,
        )
    )

    context.update(
        build_findings_context(
            session
        )
    )

    context.update(
        build_reporting_context(
            session
        )
    )

    # ========================================================
    # EVIDENCE CONTEXTS
    # ========================================================

    context.update(
        build_lineage_context(
            session
        )
    )

    context.update(
        build_trail_context(
            session
        )
    )

    context.update(
        build_traceability_context(
            session
        )
    )

    # ========================================================
    # GLOBAL CAPABILITIES
    # ========================================================

    context.update(
        build_methodology_context(
            session,
            risk_summary,
        )
    )

    context.update(
        build_narrative_context(
            session,
            risk_summary,
        )
    )

    context.update(
        build_platform_help_context()
    )

    context.update(
        getattr(session, "initialization", {})
    )

    return {
        key: value
        for key, value in context.items()
        if key != "active_tab"
    }