# ============================================================
# XAIDA 5.3
# tests/test_inquiry_router.py
# ============================================================
import pytest

from assistant.session_manager import (
    create_audit_session,
)

from assistant.prompts.system_prompt import (
    get_system_prompt,
)

# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def empty_session():

    session = create_audit_session()

    session.metadata[
        "workflow_stage"
    ] = "analysis"

    return session

def test_user_inquiry_injected():

    context = {
        "user_inquiry":
            "workflow_summary",
    }

    prompt = (
        get_system_prompt(
            context
        )
    )

    assert (
        "workflow_summary"
        in prompt
    )
def test_user_inquiry_injected():

    context = {
        "user_inquiry":
            "workflow_summary"
    }

    prompt = (
        get_system_prompt(
            context
        )
    )

    assert (
        "workflow_summary"
        in prompt
    )
    
def test_inquiry_section_present():

    prompt = (
        get_system_prompt(
            {}
        )
    )

    assert (
        "INQUIRY AWARENESS"
        in prompt
    )

def test_workflow_summary_present():

    prompt = (
        get_system_prompt(
            {
                "user_inquiry":
                    "workflow_summary"
            }
        )
    )

    assert (
        "workflow_summary"
        in prompt
    )

def test_explainability_inquiry_present():

    prompt = (
        get_system_prompt(
            {
                "user_inquiry":
                    "explainability_inquiry"
            }
        )
    )

    assert (
        "explainability_inquiry"
        in prompt
    )

