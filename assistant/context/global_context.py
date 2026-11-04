# assistant/context/global_context.py

from orchestration.workflow_engine import (
    get_current_stage,
    get_next_recommended_step,
)

def build_global_context(
    session,
):
    stage = get_current_stage(session)

    return {

        "workflow_stage":
        stage,

        "active_evidence_tab":
        session.metadata.get(
            "active_evidence_tab"
        ),

        "next_recommended_step":
        get_next_recommended_step(
            session
        ),

        "audit_name":
        (
            session.metadata.get(
                "audit_name"
            )
        ),

        "audit_status":
        (
            session.metadata.get(
                "status"
            )
        ),

        "left_panel_summary": {
            "workflow_stage": stage,
            "next_recommended_step": get_next_recommended_step(session),
            "dataset_loaded": bool(
                session.dataset.get("loaded", False)
            ),
            "audit_status": session.metadata.get("status"),
            "audit_readiness_score": session.metadata.get(
                "audit_readiness_score"
            ),
            "audit_readiness_status": session.metadata.get(
                "audit_readiness_status"
            ),
            "vertex_ai_recommendation": session.metadata.get(
                "vertex_ai_recommendation"
            ),
            "available_actions": [
                get_next_recommended_step(session)
            ],
        },

        "session_id":
        (
            session.metadata.get(
                "session_id"
            )
        ),
    }