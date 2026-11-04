# ============================================================
# AUDIT READINESS
# ============================================================

def _count_flagged_records(session):
    results = session.analysis.get("results") or {}
    analysis_df = results.get("analysis_dataframe")

    if (
        analysis_df is not None
        and "Anomaly Flag" in analysis_df.columns
    ):
        return int(analysis_df["Anomaly Flag"].astype(bool).sum())

    flags = results.get("flags")
    if flags is not None:
        return int(flags.sum())

    review_df = session.review.get("records")
    if (
        review_df is not None
        and "Anomaly Flag" in review_df.columns
    ):
        return int(review_df["Anomaly Flag"].astype(bool).sum())

    return 0


def count_explained_records(session):
    results = session.analysis.get("results") or {}

    explanations_by_record = results.get("explanation_by_record")
    if isinstance(explanations_by_record, dict):
        count = sum(
            explanation is not None
            and str(explanation).strip() != ""
            for explanation in explanations_by_record.values()
        )
        if count:
            return count

    explanations = results.get("explanations") or []
    if explanations:
        return sum(
            explanation is not None
            and str(explanation).strip() != ""
            for explanation in explanations
        )

    explainability_version = session.analysis.get(
        "explainability_version"
    )
    versions = session.analysis.get("dataset_versions", {})
    explainability_df = versions.get(explainability_version)
    if (
        explainability_df is not None
        and "Explainability Narrative" in explainability_df.columns
    ):
        narratives = (
            explainability_df["Explainability Narrative"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        return int(narratives.ne("").sum())

    explained_records = session.explainability.get(
        "explained_records",
        [],
    )
    if explained_records:
        source_records = {
            record.get("Source Record")
            for record in explained_records
            if isinstance(record, dict)
            and record.get("Source Record") is not None
        }
        return len(source_records) or len(explained_records)

    return 0


def calculate_audit_readiness(
    session,
):

    score = 100.0

    deductions = []

    rows = max(int(session.dataset.get("rows", 0) or 0), 1)

    # ========================================================
    # DATASET EXISTS
    # ========================================================

    if session.dataset.get("dataframe") is None:

        return {

            "score": 0,

            "status":
                "Not Ready",

            "audit_ready":
                False,

            "deductions": [
                {
                    "issue":
                    "Dataset Not Loaded",

                    "deduction":
                    100,
                }
            ],
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    validation_status = (
        session.dataset.get(
            "validation_status"
        )
    )

    if (
        validation_status
        and
        validation_status
        != "Completed"
    ):

        score -= 10

        deductions.append(
            {
                "issue":
                "Dataset Validation Pending",

                "deduction":
                10,
            }
        )

    # ========================================================
    # UNEXPECTED MISSING VALUES
    # POST-TREATMENT ONLY
    # ========================================================

    unexpected_missing_pct = (
        session.dataset.get(
            "unexpected_missing_percentage",
            0,
        )
    )

    unexpected_missing_pct = min(
        max(float(unexpected_missing_pct or 0), 0),
        100,
    )
    missing_penalty = round(unexpected_missing_pct * 0.15, 2)

    if missing_penalty > 0:

        score -= missing_penalty

        deductions.append(
            {
                "issue":
                (
                    f"Unexpected Missing "
                    f"({unexpected_missing_pct:.2f}%)"
                ),

                "deduction":
                missing_penalty,
            }
        )

    # ========================================================
    # DUPLICATES
    # POST-REVIEW ONLY
    # ========================================================

    duplicate_review_complete = (
        session.duplicates.get(
            "duplicate_review_complete",
            False,
        )
    )

    remaining_duplicate_count = (
        session.duplicates.get(
            "duplicate_count",
            0,
        )
    )

    if (
        not duplicate_review_complete
    ):

        duplicate_pct = min(
            max(float(remaining_duplicate_count or 0) / rows * 100, 0),
            100,
        )
        duplicate_penalty = round(duplicate_pct * 0.15, 2)

        if duplicate_penalty > 0:

            score -= duplicate_penalty

            deductions.append(
                {
                    "issue":
                    (
                        f"Duplicates Remaining "
                        f"({duplicate_pct:.2f}%)"
                    ),

                    "deduction":
                    duplicate_penalty,
                }
            )

    # ========================================================
    # ANALYSIS
    # ========================================================

    analysis_complete = (
        session.analysis.get(
            "analysis_complete",
            False,
        )
    )

    if not analysis_complete:

        score -= 20

        deductions.append(
            {
                "issue":
                "Analysis Not Completed",

                "deduction":
                20,
            }
        )

    # ========================================================
    # EXPLAINABILITY
    # ========================================================

    flagged_records = _count_flagged_records(session)
    explained_records = min(
        count_explained_records(session),
        flagged_records,
    )
    explainability_coverage = (
        explained_records / flagged_records * 100
        if flagged_records
        else 100.0
    )

    if analysis_complete:
        explainability_penalty = round(
            (100 - explainability_coverage) * 0.05,
            2,
        )
        if explainability_penalty > 0:
            score -= explainability_penalty
            deductions.append(
                {
                    "issue": (
                        "Explainability Coverage "
                        f"({explainability_coverage:.2f}%)"
                    ),
                    "deduction": explainability_penalty,
                }
            )

    # ========================================================
    # AUDIT REVIEW
    # ========================================================

    audit_review_complete = (
        session.review.get(
            "audit_review_complete",
            False,
        )
    )

    review_df = session.review.get("records")
    remaining_reviews = int(
        session.review.get("remaining_reviews", 0) or 0
    )
    if (
        review_df is not None
        and "Anomaly Flag" in review_df.columns
        and "Auditor Assessment" in review_df.columns
    ):
        outstanding = (
            review_df["Anomaly Flag"].astype(bool)
            & review_df["Auditor Assessment"]
                .fillna("")
                .astype(str)
                .str.strip()
                .eq("")
        )
        remaining_reviews = int(outstanding.sum())
    elif review_df is None and flagged_records:
        remaining_reviews = flagged_records

    review_pct_remaining = (
        min(remaining_reviews / flagged_records * 100, 100)
        if flagged_records
        else 0.0
    )
    review_penalty = round(review_pct_remaining * 0.20, 2)

    if review_penalty > 0:

        score -= review_penalty

        deductions.append(
            {
                "issue":
                (
                    f"Outstanding Reviews "
                    f"({review_pct_remaining:.2f}%)"
                ),

                "deduction":
                review_penalty,
            }
        )

    if not audit_review_complete:

        score -= 15

        deductions.append(
            {
                "issue":
                "Audit Review Not Complete",

                "deduction":
                15,
            }
        )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    score = round(
        max(
            score,
            0,
        ),
        2,
    )

    if score >= 90:

        status = (
            "Audit Ready"
        )

    elif score >= 70:

        status = (
            "Needs Review"
        )

    else:

        status = (
            "Not Ready"
        )

    return {

        "score":
            score,

        "status":
            status,

        "audit_ready":
            score >= 90,

        "explainability_coverage":
            round(explainability_coverage, 2),

        "explained_records":
            explained_records,

        "flagged_records":
            flagged_records,

        "remaining_reviews":
            remaining_reviews,

        "deductions":
            deductions,
    }