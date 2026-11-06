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
            "data_preparation_complete": True,
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
    assert readiness["score"] == 100
    assert [item["weight"] for item in readiness["breakdown"]] == [
        10,
        40,
        30,
        20,
    ]


def test_missing_data_does_not_change_workflow_completion_score():
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

    assert readiness["score"] == 100
    assert readiness["deductions"] == []
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


def test_readiness_score_includes_incomplete_audit_review():
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

    assert readiness["score"] == 80
    assert readiness["remaining_reviews"] == 1
    assert readiness["status"] == "Needs Review"
    assert not readiness["audit_ready"]


def test_uncompleted_workflow_steps_earn_only_their_assigned_points():
    session = make_session(
        rows=4,
        flagged=[False] * 4,
        explanations=[],
        assessments=[""] * 4,
    )
    session.dataset["data_preparation_complete"] = False
    session.duplicates["duplicate_count"] = 2
    session.duplicates["duplicate_review_complete"] = False
    session.analysis["analysis_complete"] = False
    session.review["audit_review_complete"] = False

    readiness = calculate_audit_readiness(session)

    assert readiness["score"] == 10
    assert [
        (item["step"], item["weight"], item["earned"])
        for item in readiness["breakdown"]
    ] == [
        ("Dataset upload", 10, 10),
        ("Preprocessing", 30, 0),
        ("Duplicate review", 10, 0),
        ("Analysis", 30, 0),
        ("Audit review", 20, 0),
    ]
    assert sum(item["weight"] for item in readiness["breakdown"]) == 100


def test_no_duplicates_assign_full_preparation_weight_to_preprocessing():
    session = make_session(
        rows=4,
        flagged=[False] * 4,
        explanations=[],
        assessments=[""] * 4,
    )
    session.dataset["data_preparation_complete"] = False
    session.analysis["analysis_complete"] = False

    readiness = calculate_audit_readiness(session)

    assert [
        (item["step"], item["weight"])
        for item in readiness["breakdown"]
    ] == [
        ("Dataset upload", 10),
        ("Preprocessing", 40),
        ("Analysis", 30),
        ("Audit review", 20),
    ]
    assert sum(item["weight"] for item in readiness["breakdown"]) == 100


def test_audit_review_has_20_percent_weight_and_is_required_for_ready_status():
    session = make_session(
        rows=4,
        flagged=[False] * 4,
        explanations=[],
        assessments=[""] * 4,
    )
    session.review["audit_review_complete"] = False

    readiness = calculate_audit_readiness(session)

    assert readiness["score"] == 80
    assert readiness["status"] == "Needs Review"
    assert not readiness["audit_ready"]
    assert readiness["breakdown"][-1] == {
        "step": "Audit review",
        "weight": 20,
        "earned": 0,
        "complete": False,
    }
    assert sum(item["weight"] for item in readiness["breakdown"]) == 100
