# ============================================================
# XAIDA 5.3
# tests/test_inquiry_router_integration.py
# ============================================================
import pytest

from assistant.session_manager import (
    create_audit_session,
)

from assistant.inquiry_router import (
    route_inquiry,
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

def test_executive_summary_maps_to_workflow_summary():

    inquiry = (
        route_inquiry(
            "executive summary"
        )
    )

    assert (
        inquiry.inquiry
        == "workflow_summary"
    )

def test_why_flagged_maps_to_explainability():

    inquiry = (
        route_inquiry(
            "why was this transaction flagged"
        )
    )

    assert (
        inquiry.inquiry
        == "explainability_inquiry"
    )