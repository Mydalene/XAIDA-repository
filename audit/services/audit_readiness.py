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
    dataset_loaded = session.dataset.get("dataframe") is not None
    data_preparation_complete = bool(
        session.dataset.get("data_preparation_complete", False)
    )
    duplicate_count = int(session.duplicates.get("duplicate_count", 0) or 0)
    duplicates_present = duplicate_count > 0
    duplicate_review_complete = bool(
        session.duplicates.get("duplicate_review_complete", False)
    )
    analysis_complete = bool(
        session.analysis.get("analysis_complete", False)
    )

    preparation_weight = 20 if duplicates_present else 30
    breakdown = [
        {
            "step": "Dataset upload",
            "weight": 20,
            "earned": 20 if dataset_loaded else 0,
            "complete": dataset_loaded,
        },
        {
            "step": "Data preparation",
            "weight": preparation_weight,
            "earned": (
                preparation_weight if data_preparation_complete else 0
            ),
            "complete": data_preparation_complete,
        },
    ]
    if duplicates_present:
        breakdown.append(
            {
                "step": "Duplicate review",
                "weight": 10,
                "earned": 10 if duplicate_review_complete else 0,
                "complete": duplicate_review_complete,
            }
        )
    breakdown.append(
        {
            "step": "Analysis",
            "weight": 50,
            "earned": 50 if analysis_complete else 0,
            "complete": analysis_complete,
        }
    )

    score = sum(item["earned"] for item in breakdown)
    deductions = [
        {
            "issue": f"{item['step']} not completed",
            "deduction": item["weight"] - item["earned"],
        }
        for item in breakdown
        if not item["complete"]
    ]

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

    audit_review_complete = bool(
        session.review.get("audit_review_complete", False)
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

    score = round(float(score), 2)
    audit_ready = (
        score == 100
        and audit_review_complete
        and remaining_reviews == 0
    )
    if audit_ready:
        status = "Audit Ready"
    elif score >= 70 or audit_review_complete:
        status = "Needs Review"
    else:
        status = "Not Ready"

    return {
        "score": score,
        "status": status,
        "audit_ready": audit_ready,
        "breakdown": breakdown,
        "explainability_coverage": round(explainability_coverage, 2),
        "explained_records": explained_records,
        "flagged_records": flagged_records,
        "remaining_reviews": remaining_reviews,
        "audit_review_complete": audit_review_complete,
        "deductions": deductions,
    }