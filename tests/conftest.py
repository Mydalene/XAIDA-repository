# tests/conftest.py

from types import SimpleNamespace

import pandas as pd
import pytest

from assistant.session_manager import (
    create_audit_session,
)


@pytest.fixture(autouse=True)
def isolate_evaluation_store(tmp_path, monkeypatch):
    monkeypatch.setenv("XAIDA_REQUIRE_AUTH", "false")
    monkeypatch.setenv(
        "XAIDA_EVALUATION_DB_PATH",
        str(tmp_path / "xaida_evaluations.sqlite3"),
    )


@pytest.fixture
def test_session():

    session = create_audit_session()

    session.metadata["workflow_stage"] = "reporting"

    session.dataset.update(
        {
            "dataset_name": "Regression Dataset",
            "rows": 2000,
            "data_preparation_complete": True,
            "unexpected_missing_percentage": 0,
        }
    )

    session.duplicates.update(
        {
            "duplicate_count": 20,
            "duplicate_groups": 5,
        }
    )

    session.analysis.update(
        {
            "risk_level": "High",
        }
    )

    return session

@pytest.fixture
def mock_session():

    return SimpleNamespace(

        metadata={
            "workflow_stage": "analysis",
            "active_tab": "Analysis",
        },

        dataset={
            "dataset_name": "Test Dataset",
            "dataset_version": "V1",
            "rows": 100,
            "columns": 5,
            "column_names": [
                "A",
                "B",
                "C",
                "D",
                "E",
            ],
            "column_types": {},
            "data_preparation_complete": True,
            "unexpected_missing_percentage": 0,
            "dataset_lineage_summary": "",
            "validation_status": "Completed",
            "dataframe": pd.DataFrame(
                {
                    "A": [1, 2],
                    "B": ["x", "y"],
                    "C": [10.5, 20.5],
                }
            ),

        },

        duplicates={
            "duplicate_count": 5,
            "duplicate_groups": 2,
            "duplicate_review_complete": True,
            "strategy": "Remove Duplicate Copies",
            "removed_duplicate_records": None,
        },

        analysis={
            "analysis_complete": True,
            "risk_level": "Medium",
            "report_generated": False,
            "dataset_version_metadata": {},
            "results": {
                "threshold": 0.80,
            },
        },

        explainability={
            "narratives": [],
            "explained_records": [],
            "top_features": [],
        },

        review={
            "audit_review_complete": False,
            "remaining_reviews": 0,
            "review_complete": False,
        },

        findings={
            "validated": [],
            "open": [],
            "findings_dataframe": None,
        },

        audit_log=[],
    )

@pytest.fixture
def sample_dataframe():

    return pd.DataFrame(
        {
            "Amount": [100, 200],
            "Vendor": [
                "ABC",
                "XYZ",
            ],
            "Risk": [
                0.10,
                0.25,
            ],
        }
    )
