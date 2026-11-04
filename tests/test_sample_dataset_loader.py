import pandas as pd

from assistant.session_manager import create_audit_session
from dataset.sample_dataset_loader import load_sample_dataset


def test_load_sample_dataset_from_dataset_stage(monkeypatch):
    from dataset import sample_dataset_loader

    monkeypatch.setattr(
        sample_dataset_loader.st,
        "session_state",
        {},
    )
    session = create_audit_session()
    session.conversation.append(
        {"role": "assistant", "content": "Existing session message."}
    )
    session.analysis["results"] = {"retained": True}

    dataframe = load_sample_dataset(session, "Accounts Payable")

    assert isinstance(dataframe, pd.DataFrame)
    assert not dataframe.empty
    assert session.dataset["dataframe"].equals(dataframe)
    assert session.dataset["loaded"] is True
    assert session.metadata["workflow_stage"] == "dataset"
    assert session.analysis["dataset_version"] == 1
    assert session.conversation == [
        {"role": "assistant", "content": "Existing session message."}
    ]
    assert session.analysis["results"] == {"retained": True}
