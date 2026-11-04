import pandas as pd

from assistant.session_manager import create_audit_session
from dataset import data_preparation_service


def test_preparation_completes_without_calculating_quality_score(monkeypatch):
    session = create_audit_session()
    session.dataset["dataframe"] = pd.DataFrame(
        {
            "Amount": [10.0, None, 30.0],
            "Category": ["A", "B", "C"],
        }
    )
    monkeypatch.setattr(
        data_preparation_service,
        "create_dataset_version",
        lambda **kwargs: 2,
    )
    monkeypatch.setattr(
        data_preparation_service,
        "log_audit_event",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        data_preparation_service,
        "calculate_audit_readiness",
        lambda _session: {"score": 100},
    )

    result = data_preparation_service.run_data_preparation(session)

    assert session.dataset["data_preparation_complete"] is True
    assert session.dataset["validation_status"] == "Completed"
    assert session.dataset["validation_results"]["valid"] is True
    assert session.dataset["unexpected_missing_percentage"] == 33.33
    assert "quality_score" not in session.dataset
    assert "quality_score_breakdown" not in session.dataset
    assert "quality_score_methodology" not in session.dataset
    assert "quality_score" not in result
