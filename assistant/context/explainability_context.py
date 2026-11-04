from orchestration.workflow_engine import (
    get_next_recommended_step,
)

from audit.services.audit_readiness import (
    count_explained_records,
)


# ===================================
# EXPLAINABILITY
# ===================================

def build_explainability_context(
    session,
    top_features,
):

    selected_row = (
        session.explainability.get(
            "selected_row",
            {},
        )
        or {}
    )

    stored_top_features = (
        session.explainability.get(
            "top_features"
        )
    )

    top_feature_drivers = []

    if (
        stored_top_features is not None
        and hasattr(
            stored_top_features,
            "head",
        )
    ):

        top_feature_drivers = (
            stored_top_features
            .head(10)
            .to_dict("records")
        )

    results = session.analysis.get("results") or {}
    shap_contribution_details = (
        results.get("shap_contribution_details") or []
    )
    explained_record_count = count_explained_records(session)

    flagged_record_count = 0
    analysis_df = results.get("analysis_dataframe")
    if (
        analysis_df is not None
        and "Anomaly Flag" in analysis_df.columns
    ):
        flagged_record_count = int(
            analysis_df["Anomaly Flag"].astype(bool).sum()
        )
    elif results.get("flags") is not None:
        flagged_record_count = int(results["flags"].sum())

    explained_record_count = min(
        explained_record_count,
        flagged_record_count,
    )
    explainability_coverage = (
        explained_record_count / flagged_record_count * 100
        if flagged_record_count
        else 100.0
    )
    workflow_stage = session.metadata.get("workflow_stage")
    explainability_steps = [
        "Review Transaction Explanations",
        "Select Flagged Transaction",
        "Review Explainability Narrative",
        "Review Top Feature Drivers",
        "Review SHAP Details",
    ]
    if workflow_stage == "explainability":
        explainability_steps.append("Open Audit Review")
    elif workflow_stage == "audit_review":
        explainability_steps.append(
            get_next_recommended_step(session)
        )

    return {

        # ===================================
        # EXPLAINABILITY ENGINE
        # ===================================

        "explainability_engine":
            "SHAP",

        "explainability_model":
            "Isolation Forest",

        # ===================================
        # SELECTED TRANSACTION
        # ===================================

        "selected_record":
        (
            session.explainability.get(
                "selected_record"
            )
        ),

        "selected_risk_score":
        (
            session.explainability.get(
                "selected_risk_score"
            )
        ),

        "selected_key_drivers":
        (
            session.explainability.get(
                "selected_key_drivers"
            )
        ),

        "selected_transaction":
            selected_row,

        # ===================================
        # EXPLANATIONS
        # ===================================

        "explained_records":
        (
            session.explainability.get(
                "explained_records",
                [],
            )
        ),

        "explainability_narratives":
        (
            session.explainability.get(
                "narratives",
                [],
            )
        ),

        "shap_contribution_details":
            shap_contribution_details[:50],

        # ===================================
        # FEATURE DRIVERS
        # ===================================

        "top_features":
            top_features,

        "top_feature_drivers":
            top_feature_drivers,

        "top_driver_count":
        (
            len(top_features)
            if top_features is not None
            else 0
        ),

        # ===================================
        # EXPLAINABILITY COVERAGE
        # ===================================

        "explained_record_count":
            explained_record_count,

        "flagged_record_count":
            flagged_record_count,

        "narrative_count":
        (
            len(
                session.explainability.get(
                    "narratives",
                    [],
                )
            )
        ),

        "explainability_coverage":
            f"{explainability_coverage:.2f}%",

        "explainability_dataset_version":
            session.analysis.get(
                "explainability_version"
            ),

        "explainability_version":
            session.analysis.get(
                "explainability_version"
            ),

        # ===================================
        # EXPLAINABILITY NAVIGATION
        # ===================================

        "explainability_sections":
        [
            "Transaction Explanations",
            "Explainability Narrative",
            "Top Feature Drivers",
            "SHAP Details",
        ],

        "explainability_workflow_steps":
            explainability_steps,

        "explainability_navigation_help":
            (
                "Review transaction explanations, select a flagged "
                "transaction, inspect its key drivers and narrative, then "
                f"follow the current workflow step: {explainability_steps[-1]}."
            ),

        # ===================================
        # STAGE STATUS
        # ===================================

        "analysis_complete":
        (
            session.analysis.get(
                "analysis_complete",
                False,
            )
        ),

        "duplicate_review_complete":
        (
            session.duplicates.get(
                "duplicate_review_complete",
                False,
            )
        ),

        "audit_review_available":
        (
            session.analysis.get(
                "analysis_complete",
                False,
            )
        ),
    }