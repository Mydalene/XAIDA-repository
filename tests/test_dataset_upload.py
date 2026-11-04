from io import BytesIO

import pandas as pd
import pytest

from assistant.session_manager import create_audit_session
from ui.evidence import dataset_upload


class UploadedDataset(BytesIO):
    def __init__(self, content, name):
        super().__init__(content)
        self.name = name


def make_uploaded_dataset(dataframe, filename):
    content = BytesIO()
    if filename.lower().endswith(".csv"):
        dataframe.to_csv(content, index=False)
    else:
        dataframe.to_excel(content, index=False)
    return UploadedDataset(content.getvalue(), filename)


@pytest.mark.parametrize(
    "filename",
    ["transactions.csv", "transactions.CSV", "transactions.xlsx"],
)
def test_upload_dataset_loads_csv_and_xlsx(monkeypatch, filename):
    expected = pd.DataFrame(
        {
            "transaction_id": [1, 2],
            "amount": [12.5, 20.0],
        }
    )
    uploaded_file = make_uploaded_dataset(expected, filename)
    state = {}
    monkeypatch.setattr(dataset_upload.st, "session_state", state)
    monkeypatch.setattr(
        dataset_upload.st,
        "file_uploader",
        lambda *args, **kwargs: uploaded_file,
    )
    monkeypatch.setattr(dataset_upload.st, "success", lambda *args, **kwargs: None)
    monkeypatch.setattr(dataset_upload.st, "error", lambda *args, **kwargs: None)
    monkeypatch.setattr(dataset_upload.st, "rerun", lambda: None)

    session = create_audit_session()
    session.conversation.append(
        {"role": "assistant", "content": "Existing session message."}
    )
    session.analysis["results"] = {"retained": True}
    dataset_upload.render_dataset_upload(session)

    pd.testing.assert_frame_equal(session.dataset["dataframe"], expected)
    assert session.conversation == [
        {"role": "assistant", "content": "Existing session message."}
    ]
    assert session.analysis["results"] == {"retained": True}
    assert session.dataset["loaded"] is True
    assert session.dataset["rows"] == 2
    assert session.dataset["columns"] == 2
    assert session.dataset["parsing_status"] == "Completed"
    assert session.dataset["validation_status"] == "Pending"
    assert session.analysis["dataset_version"] == 1
    assert session.metadata["workflow_stage"] == "dataset"
    assert state["active_tab"] == "Dataset"


def test_invalid_upload_does_not_reset_existing_analysis(monkeypatch):
    state = {}
    uploaded_file = UploadedDataset(b"not a supported dataset", "notes.txt")
    monkeypatch.setattr(dataset_upload.st, "session_state", state)
    monkeypatch.setattr(
        dataset_upload.st,
        "file_uploader",
        lambda *args, **kwargs: uploaded_file,
    )

    session = create_audit_session()
    session.analysis["analysis_complete"] = True

    dataset_upload.render_dataset_upload(session)

    assert session.analysis["analysis_complete"] is True
    assert session.dataset.get("loaded", False) is False
    assert state["xaida_action_dialog"]["level"] == "error"
    assert "Unsupported dataset format" in state["xaida_action_dialog"]["message"]
    assert session.dataset["parsing_status"] == "Failed"


def test_dataset_parser_error_is_shown_without_raw_exception_details(
    monkeypatch,
):
    state = {}
    uploaded_file = UploadedDataset(
        b"not,a,valid\n\xff",
        "transactions.csv",
    )
    monkeypatch.setattr(dataset_upload.st, "session_state", state)
    monkeypatch.setattr(
        dataset_upload.st,
        "file_uploader",
        lambda *args, **kwargs: uploaded_file,
    )

    session = create_audit_session()
    dataset_upload.render_dataset_upload(session)

    message = state["xaida_action_dialog"]["message"]
    assert state["xaida_action_dialog"]["level"] == "error"
    assert "could not be processed" in message
    assert "\xff" not in message
    assert session.dataset["parsing_status"] == "Failed"
