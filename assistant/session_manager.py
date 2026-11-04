import uuid
from datetime import datetime

import streamlit as st

from assistant.audit_session import (
    AuditSession,
)
from assistant.session_persistence import (
    SESSION_QUERY_PARAM,
    authenticated_owner_hash,
    delete_active_session,
    get_or_create_session,
    save_active_session,
    session_storage_enabled,
)
from audit.audit_logger import (
    log_audit_event,
)

# ============================================================
# GET SESSION
# ============================================================

def get_session():
    """
    Returns the active XAIDA AuditSession.

    Creates and stores a new session if one does not yet exist.
    Acts as the single entry point for session retrieval
    throughout the application.
    """

    session = get_or_create_session(create_audit_session)

    if (
        session.metadata.get("workflow_stage") == "initialization"
        and not any(
            event.get("stage") == "Initialization"
            and event.get("action") == "Audit Initialized"
            for event in session.audit_log
            if isinstance(event, dict)
        )
    ):
        log_audit_event(
            session,
            stage="Initialization",
            action="Audit Initialized",
            details="New audit session created.",
        )

    return session

# ============================================================
# INITIALIZATION
# ============================================================

def create_default_initialization_state():

    return {

        "initialized": True,

        "dataset_selected": False,

        "dataset_loaded": False,

        "upload_method":         None,

        "dataset_source": None,

        "sample_dataset": None,

        "initialization_complete": False,

        "reset_reason": "new_analysis",
    }

# ============================================================
# DEFAULT STATE FACTORIES
# ============================================================  

def create_default_duplicates_state():
    return {
        "duplicate_count": 0,
        "duplicate_groups": 0,
        "strategy": None,
        "records_removed": 0,
        "duplicate_review_complete": False,
        "duplicate_records": None,
        "duplicate_removal_schedule": [],
    }


def create_default_analysis_state():
    return {
        "analysis_complete": False,
        "analysis_dataset": None,
        "analysis_dataset_summary": {},
        "dataset_version": 0,
        "analysis_version": 0,
        "analysis_required": False,
        "latent_features": None,
        "risk_scores": None,
        "risk_distribution": {},
        "risk_level": None,
    }


def create_default_findings_state():

    return {

        "findings_dataframe": None,

        "findings_locked": False,
        "source_dataset_version": None,
        "findings_dataset_version": None,
        "report_dataset_version": None,

        "open": [],
        "under_review": [],
        "validated": [],
        "dismissed": [],
        "resolved": [],
    }

def create_default_explainability_state():
    return {
        "shap_values": None,
        "top_features": None,
        "narratives": [],
    }

def create_default_review_state():

    return {

        "mode": None,

        "review_dataset": None,

        "review_version": None,

        "records": None,

        "summary": {

            "confirmed_anomaly": 0,

            "potential_finding": 0,

            "false_positive": 0,

            "normal_transaction": 0,

            "requires_investigation": 0,

        },
    }

def create_default_reporting_state():
    return {
        "executive_summary": None,
        "recommendations": [],
        "excel_ready": False,
        "pdf_ready": False,
    }

# ============================================================
# CREATE AUDIT SESSION
# ============================================================

def create_audit_session():

    # ========================================================
    # INITIALIZATION
    # ========================================================

    session = AuditSession()
    session.evaluation_session_id = str(uuid.uuid4())

    # ========================================================
    # METADATA
    # ========================================================
    session.metadata = {
        "session_id": str(uuid.uuid4()),
        "audit_name": "New Audit",
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "workflow_stage": "initialization",
        "status": "active",

        "welcome_shown": False,
        "completion_dialog_dismissed": False,
    }
    

    # ========================================================
    # AUDIT LOG
    # ========================================================

    session.audit_log = []


    session.initialization = (
        create_default_initialization_state()
    )

    log_audit_event(
        session,
        stage="Initialization",
        action="Audit Initialized",
        details="New audit session created.",
    )


    # ========================================================
    # DATASET
    # ========================================================

    session.dataset = {
        "dataset_name":
            None,

        "rows":
            0,

        "columns":
            0,

        "data_preparation_complete":
            False,

        "unexpected_missing_percentage":
            None,

        "dataframe":
            None,

        "profile":
            {},
    }

    # ========================================================
    # DUPLICATES
    # ========================================================

    session.duplicates = (
        create_default_duplicates_state()
    )

    # ========================================================
    # ANALYSIS
    # ========================================================

    session.analysis = (
        create_default_analysis_state()
    )

    # ========================================================
    # EXPLAINABILITY
    # ========================================================

    session.explainability = (
        create_default_explainability_state()
    )

    # ========================================================
    # AUDIT REVIEW
    # ========================================================

    session.review = (
        create_default_review_state()
    )


    # ========================================================
    # FINDINGS
    # ========================================================

    session.findings = (
        create_default_findings_state()
    )

    # ========================================================
    # REPORTING
    # ========================================================

    session.reporting = (
        create_default_reporting_state()
    )

    # ========================================================
    # CONVERSATION
    # ========================================================

    session.conversation = []

    return session


# ============================================================
# SESSION HELPERS
# ============================================================

def session_exists():

    return (
        "audit_session"
        in st.session_state
    )

def reset_session():

    current_session = st.session_state.get("audit_session")
    if current_session is not None:
        delete_active_session(current_session)

    session = create_audit_session()

    st.session_state[
        "audit_session"
    ] = session

    if session_storage_enabled():
        st.session_state["xaida_session_owner_hash"] = (
            authenticated_owner_hash()
        )
        st.query_params[SESSION_QUERY_PARAM] = session.metadata["session_id"]

    return session


# ============================================================
# SESSION UTILITIES
# ============================================================

def touch_session(
    session,
):

    session.metadata[
        "last_updated"
    ] = datetime.now()


def add_audit_entry(
    session,
    stage,
    action,
    details="",
):

    session.audit_log.append(
        {
            "timestamp":
                datetime.now(),

            "stage":
                stage,

            "action":
                action,

            "details":
                details,
        }
    )

    touch_session(
        session
    )

def save_session():
    session = st.session_state.get("audit_session")
    if session is not None:
        save_active_session(session)
