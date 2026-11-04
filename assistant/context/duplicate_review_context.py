def build_duplicate_review_context(
    session,
):

    duplicate_count = (
        session.duplicates.get(
            "duplicate_count",
            0,
        )
    )

    duplicate_groups = (
        session.duplicates.get(
            "duplicate_groups",
            0,
        )
    )

    outcome = session.analysis.get(
        "analysis_dataset_summary",
        {},
    ) or {}
    removed_records = session.duplicates.get(
        "removed_duplicate_records"
    )
    removed_record_sample = (
        removed_records.to_dict("records")
        if removed_records is not None
        else []
    )
    strategy = session.duplicates.get("strategy")
    strategy_result = {
        "strategy": strategy,
        "review_complete": session.duplicates.get(
            "duplicate_review_complete",
            False,
        ),
        "original_records": outcome.get("original_records"),
        "records_removed": outcome.get(
            "records_removed",
            session.duplicates.get("records_removed", 0),
        ),
        "records_retained": outcome.get("records_retained"),
        "rationale_recorded": session.duplicates.get(
            "strategy_rationale"
        ),
        "decision_rationale": (
            session.duplicates.get("strategy_rationale")
            or "No separate auditor rationale for choosing this strategy "
            "is recorded in the session."
        ),
    }

    quality_issues = []

    if duplicate_count > 0:

        quality_issues.append(
            {
                "issue":
                "Duplicate Records",

                "count":
                duplicate_count,

                "groups":
                duplicate_groups,

                "status":
                (
                    "Reviewed"
                    if
                    session.duplicates.get(
                        "duplicate_review_complete",
                        False,
                    )
                    else
                    "Pending Review"
                ),
            }
        )

    return {

        "duplicate_count":
        duplicate_count,

        "duplicate_groups":
        duplicate_groups,

        "duplicate_strategy":
            strategy,

        "duplicate_strategy_result":
            strategy_result,

        "duplicate_review_complete":
        session.duplicates.get(
            "duplicate_review_complete",
            False,
        ),

        "duplicate_evidence_summary":
            outcome,

        "removed_duplicate_record_sample":
            removed_record_sample,

        "duplicate_removal_schedule":
            session.duplicates.get("duplicate_removal_schedule", []),

        "duplicate_records":
        (
            session.duplicates.get(
                "duplicate_records"
            )
            .to_dict(
                "records"
            )
            if
            session.duplicates.get(
                "duplicate_records"
            ) is not None
            else []
        ),

        "quality_issues":
        quality_issues,
    }