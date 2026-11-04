from types import SimpleNamespace

import pandas as pd

from audit.services.audit_readiness import (
    calculate_audit_readiness,
)


def make_session(
    rows,
    flagged,
    explanations,
    assessments,
):
    analysis_df = pd.DataFrame(
        {
            "Anomaly Flag": flagged,
            "Risk Score": [0.8 if value else 0.1 for value in flagged],
        }
    )
    review_df = analysis_df.copy()
    review_df["Auditor Assessment"] = assessments

    return SimpleNamespace(
        dataset={
            "dataframe": analysis_df,
            "rows": rows,
            "validation_status": "Completed",
            "unexpected_missing_percentage": 0,
        },
        duplicates={
            "duplicate_review_complete": True,
            "duplicate_count": 0,
        },
        analysis={
            "analysis_complete": True,
            "results": {
                "analysis_dataframe": analysis_df,
                "explanations": explanations,
            },
            "dataset_versions": {},
        },
        explainability={
            "explained_records": [],
            "narratives": [],
        },
        review={
            "records": review_df,
            "audit_review_complete": True,
            "remaining_reviews": 0,
        },
    )


def test_explainability_coverage_is_based_on_flagged_records():
    session = make_session(
        rows=4,
        flagged=[True, True, True, True],
        explanations=["first", "second"],
        assessments=[
            "Confirmed Anomaly",
            "Confirmed Anomaly",
            "Confirmed Anomaly",
            "Confirmed Anomaly",
        ],
    )

    readiness = calculate_audit_readiness(session)

    assert readiness["flagged_records"] == 4
    assert readiness["explained_records"] == 2
    assert readiness["explainability_coverage"] == 50
    assert readiness["score"] == 97.5


def test_audit_readiness_retains_its_missing_data_deduction_without_quality_score():
    session = make_session(
        rows=4,
        flagged=[False, False, False, False],
        explanations=[],
        assessments=[""] * 4,
    )
    session.dataset["unexpected_missing_percentage"] = 10
    session.duplicates["duplicate_review_complete"] = True
    session.review["audit_review_complete"] = True

    readiness = calculate_audit_readiness(session)

    assert readiness["score"] == 98.5
    assert readiness["deductions"] == [
        {
            "issue": "Unexpected Missing (10.00%)",
            "deduction": 1.5,
        }
    ]
    assert "quality_score" not in session.dataset


def test_explainability_coverage_uses_full_results_not_display_sample():
    flags = [True] * 100
    session = make_session(
        rows=100,
        flagged=flags,
        explanations=[f"drivers-{index}" for index in range(100)],
        assessments=["Confirmed Anomaly"] * 100,
    )
    session.explainability["explained_records"] = [
        {"Source Record": index, "Key Drivers": f"drivers-{index}"}
        for index in range(50)
    ]
    session.analysis["results"]["explanation_by_record"] = {
        index: f"drivers-{index}"
        for index in range(100)
    }

    readiness = calculate_audit_readiness(session)

    assert readiness["flagged_records"] == 100
    assert readiness["explained_records"] == 100
    assert readiness["explainability_coverage"] == 100


def test_review_penalty_uses_unreviewed_flagged_records():
    flags = [True, True] + [False] * 98
    assessments = ["Confirmed Anomaly", ""] + [""] * 98
    session = make_session(
        rows=100,
        flagged=flags,
        explanations=["first", "second"],
        assessments=assessments,
    )
    session.review["audit_review_complete"] = False

    readiness = calculate_audit_readiness(session)

    outstanding = next(
        item
        for item in readiness["deductions"]
        if item["issue"].startswith("Outstanding Reviews")
    )
    assert outstanding["deduction"] == 10
