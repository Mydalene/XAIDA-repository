from assistant import session_manager
from orchestration.workflow_engine import (
    DATASET,
    INITIALIZATION,
    can_transition,
    transition_to,
)
from assistant.session_validator import validate_session


def test_new_audit_session_starts_at_initialization():
    session = session_manager.create_audit_session()

    assert session.metadata["workflow_stage"] == "initialization"
    assert session.audit_log[0]["stage"] == "Initialization"
    assert session.audit_log[0]["action"] == "Audit Initialized"
    assert session.dataset["dataframe"] is None
    assert session.dataset["rows"] == 0
    assert session.dataset["columns"] == 0


def test_get_session_preserves_initialization_stage(monkeypatch):
    legacy_session = session_manager.create_audit_session()
    legacy_session.metadata["workflow_stage"] = "initialization"
    legacy_session.audit_log = []
    state = {"audit_session": legacy_session}
    monkeypatch.setattr(session_manager.st, "session_state", state)

    session = session_manager.get_session()

    assert session is legacy_session
    assert session.metadata["workflow_stage"] == "initialization"
    assert session.audit_log[0]["action"] == "Audit Initialized"


def test_get_session_creates_and_stores_initialization_session(monkeypatch):
    state = {}
    monkeypatch.setattr(session_manager.st, "session_state", state)

    session = session_manager.get_session()

    assert state["audit_session"] is session
    assert session.metadata["workflow_stage"] == "initialization"


def test_auditor_sessions_keep_independent_in_memory_datasets(monkeypatch):
    first_state = {}
    second_state = {}
    monkeypatch.setattr(
        session_manager.st,
        "session_state",
        first_state,
    )
    first_session = session_manager.get_session()
    first_session.dataset["dataset_name"] = "first-auditor.csv"

    monkeypatch.setattr(
        session_manager.st,
        "session_state",
        second_state,
    )
    second_session = session_manager.get_session()
    second_session.dataset["dataset_name"] = "second-auditor.csv"

    assert first_session is not second_session
    assert first_state["audit_session"] is first_session
    assert second_state["audit_session"] is second_session
    assert first_session.dataset["dataset_name"] == "first-auditor.csv"
    assert second_session.dataset["dataset_name"] == "second-auditor.csv"


def test_initialization_transitions_to_dataset():
    session = session_manager.create_audit_session()

    assert session.metadata["workflow_stage"] == INITIALIZATION
    is_valid, errors = validate_session(session)
    assert is_valid, errors
    assert can_transition(session, DATASET)

    transition_to(session, DATASET)

    assert session.metadata["workflow_stage"] == DATASET
