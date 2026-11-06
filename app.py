# ============================================================
# XAIDA 5.0 APPLICATION
# ============================================================

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _chatbot_error_message(error):
    error_type = type(error).__name__
    if isinstance(error, RuntimeError):
        message = str(error)
        if message.startswith(
            (
                "XAIDA Vertex AI Assistant is not configured.",
                "XAIDA Vertex AI Assistant data transfer is disabled.",
                "GOOGLE_CLOUD_PROJECT must be the actual Google Cloud project ID",
            )
        ):
            return message

    messages = {
        "DefaultCredentialsError": (
            "Google Cloud credentials are not configured. For local use, "
            "install Google Cloud CLI and run "
            "`gcloud auth application-default login`. On Cloud Run, use a "
            "service account with Vertex AI User access."
        ),
        "RefreshError": (
            "Google Cloud credentials could not be refreshed. Re-authenticate "
            "with `gcloud auth application-default login`, or check the "
            "Cloud Run service account credentials."
        ),
        "Unauthenticated": (
            "Vertex AI authentication failed. Check the Cloud Run service "
            "account and its permissions."
        ),
        "PermissionDenied": (
            "Vertex AI denied access. Check that the Cloud Run service "
            "account has Vertex AI User access to the configured project."
        ),
        "NotFound": (
            "The configured Vertex AI model or project resource was not "
            "found. Check the model name, project, and region."
        ),
        "ResourceExhausted": (
            "Vertex AI quota was reached. Check project quota and try again."
        ),
        "ServiceUnavailable": (
            "XAIDA could not connect to Vertex AI. Check network access and "
            "try again."
        ),
        "DeadlineExceeded": (
            "The Vertex AI request timed out. Check network access and try "
            "again."
        ),
        "InvalidArgument": (
            "Vertex AI rejected the request. Check model and request "
            "configuration."
        ),
    }
    return messages.get(
        error_type,
        "XAIDA could not complete the request. Check the AI service "
        "configuration or contact the application administrator.",
    )


st.set_page_config(
    page_title="XAIDA",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.access_control import (
    enforce_access_control,
    authentication_required,
    oidc_user_logged_in,
)

enforce_access_control()

if not st.session_state.get(
    "xaida_security_statement_acknowledged",
    False,
):
    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        wrap=True,
    ):
        with st.container(
            width=900,
            border=True,
            key="xaida_security_statement_card",
        ):
            st.title(
                "XAIDA Security and Confidentiality Statement",
                icon=":material/verified_user:",
            )
            st.caption(
                "Please review how XAIDA handles audit information before "
                "starting your session."
            )
            security_statement = (
                Path(__file__)
                .with_name("SECURITY_STATEMENT.md")
                .read_text(encoding="utf-8")
            )
            st.markdown(security_statement)
            st.divider()
            acknowledged = st.checkbox(
                "I have read and understood the XAIDA Security Statement.",
                key="xaida_security_statement_ack",
            )
            if st.button(
                "Continue to XAIDA",
                key="xaida_start_session",
                type="primary",
                disabled=not acknowledged,
                icon=":material/arrow_forward:",
            ):
                st.session_state[
                    "xaida_security_statement_acknowledged"
                ] = True
                st.rerun()
    st.stop()

from assistant.action_router import (
    execute_action,
)
from assistant.completion_summary import (
    build_completion_summary,
)
from assistant.vertex_ai_assistant import (
    XaidaVertexAIAssistant,
)
from assistant.evaluation_store import (
    GROUNDING_RATINGS,
    record_feedback,
)
from assistant.conversation_manager import (
    get_feedback_exchange,
)
from assistant.session_manager import (
    get_session,
    save_session,
)
from assistant.session_persistence import (
    SessionExpiredError,
    SessionPersistenceError,
    SessionUnavailableError,
    delete_active_session,
    session_storage_enabled,
)
from dataset.duplicate_resolution import (
    remove_rows,
)
from dataset.sample_dataset_loader import (
    load_sample_dataset,
)
from orchestration.workflow_engine import (
    get_next_recommended_step,
)
from ui.evidence.dataset_upload import (
    render_dataset_upload,
)
from ui.evidence_panel import (
    render_evidence_panel,
)
from ui.action_dialog import (
    ACTION_DIALOG_KEY,
    queue_action_confirmation,
    queue_action_message,
    render_action_dialog,
    render_action_notification,
)

logger = logging.getLogger(__name__)

# ============================================================
# SESSION
# ============================================================

try:
    session = get_session()
except SessionPersistenceError as error:
    st.error(str(error))
    if isinstance(error, (SessionExpiredError, SessionUnavailableError)):
        if st.button("Start a new analysis", key="xaida_expired_session"):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()
    st.stop()


def _action_outcome(result, title, fallback_message):
    if not isinstance(result, dict) or not result.get("success", False):
        message = (
            result.get("message", "The requested action could not be completed.")
            if isinstance(result, dict)
            else "The requested action returned an invalid result."
        )
        return {
            "title": f"{title} failed",
            "message": message,
            "level": "error",
        }
    return {
        "title": title,
        "message": result.get("message") or fallback_message,
        "level": "success",
    }


def _render_new_analysis_button():
    if st.button(
        "New analysis",
        key="xaida_new_analysis",
        icon=":material/add:",
        width="stretch",
    ):
        queue_action_confirmation(
            title="Start a new analysis?",
            message=(
                "Starting a new analysis deletes all data in the current "
                "session. This action cannot be undone."
            ),
            confirm_label="Start new analysis",
            action="new_analysis",
            success_message="A new audit analysis session is ready.",
        )
        st.rerun()


def _handle_action_confirmation(pending):
    action = pending["action"]
    if action == "remove_manual_duplicates":
        positions = st.session_state.get("pending_duplicate_rows", [])
        duplicates = session.duplicates.get("duplicate_records")
        if not isinstance(duplicates, pd.DataFrame) or not positions:
            return {
                "title": "Removal unavailable",
                "message": "No selected duplicate rows are available for removal.",
                "level": "error",
            }
        if any(
            position < 0 or position >= len(duplicates)
            for position in positions
        ):
            return {
                "title": "Removal unavailable",
                "message": (
                    "The duplicate selection is no longer valid. Select the "
                    "rows again."
                ),
                "level": "error",
            }

        selected_indices = duplicates.iloc[positions].index.tolist()
        remove_rows(session, selected_indices)
        session.duplicates["duplicate_review_complete"] = True
        session.duplicates["selected_duplicate_rows"] = []
        session.duplicates["selected_duplicate_count"] = 0
        st.session_state["pending_duplicate_rows"] = []
        st.session_state["pending_duplicate_count"] = 0
        return {
            "title": "Duplicates removed",
            "message": pending["success_message"],
            "level": "success",
        }

    if action in {"exit_delete_audit", "logout_exit"}:
        try:
            if (
                action == "exit_delete_audit"
                or session_storage_enabled()
            ):
                delete_active_session(session)
        except SessionPersistenceError as error:
            return {
                "title": "Audit data could not be deleted",
                "message": str(error),
                "level": "error",
            }
        if action == "logout_exit" and authentication_required():
            if oidc_user_logged_in():
                st.logout()
        st.session_state.clear()
        st.query_params.clear()
        return {
            "title": (
                "Logged out and audit data deleted"
                if action == "logout_exit" and authentication_required()
                else "Audit data deleted"
            ),
            "message": pending["success_message"],
            "level": "success",
        }

    try:
        result = execute_action(action, session)
    except SessionPersistenceError as error:
        return {
            "title": f"{pending['title']} failed",
            "message": str(error),
            "level": "error",
        }
    if action == "new_analysis" and isinstance(result, dict) and result.get("success"):
        outcome = _action_outcome(
            result,
            pending["title"],
            pending["success_message"],
        )
        outcome["message"] = pending["success_message"]
        return outcome
    return _action_outcome(
        result,
        pending["title"],
        pending["success_message"],
    )


def _run_action_with_popup(action, title, fallback_message):
    result = execute_action(action, session)
    outcome = _action_outcome(result, title, fallback_message)
    queue_action_message(
        outcome["title"],
        outcome["message"],
        outcome["level"],
    )


# ============================================================
# VERTEX AI ASSISTANT
# ============================================================

if "vertex_ai_assistant" not in st.session_state:

    st.session_state.vertex_ai_assistant = (
        XaidaVertexAIAssistant()
    )

vertex_ai_assistant = st.session_state.vertex_ai_assistant

st.session_state.setdefault("xaida_chat_open", False)
def close_xaida_chat():
    st.session_state["xaida_chat_open"] = False


@st.dialog(
    "🤖 XAIDA Vertex AI Assistant",
    on_dismiss=close_xaida_chat,
)
def xaida_chat_dialog():
    st.markdown(
        """
        <div class="xaida-chat-intro">
            <span class="xaida-chat-eyebrow">POWERED BY VERTEX AI</span>
            <div class="xaida-chat-title">Evidence, made clearer.</div>
            <div class="xaida-chat-subtitle">
                Ask about this audit, its evidence, or the next workflow step.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(height=580, autoscroll=True):
        if not session.conversation:
            with st.chat_message("assistant"):
                st.markdown(
                    "Welcome to XAIDA Vertex AI Assistant. Ask about the "
                    "current audit, its evidence, or the next workflow step."
                )

        for message in session.conversation:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                interaction_id = message.get("interaction_id")
                if message["role"] == "assistant" and interaction_id:
                    if message.get("feedback_submitted"):
                        st.caption("Thank you for evaluating this response.")
                    else:
                        with st.expander("Rate this response"):
                            with st.form(
                                key=f"xaida_feedback_{interaction_id}"
                            ):
                                grounding_rating = st.radio(
                                    "Was the response grounded in the audit evidence?",
                                    GROUNDING_RATINGS,
                                    horizontal=True,
                                )
                                helpfulness_rating = st.slider(
                                    "How helpful was it?",
                                    min_value=1,
                                    max_value=5,
                                    value=3,
                                )
                                submitted = st.form_submit_button(
                                    "Submit feedback"
                                )
                            if submitted:
                                try:
                                    exchange = get_feedback_exchange(
                                        session,
                                        interaction_id,
                                    )
                                    if exchange is None:
                                        raise ValueError(
                                            "The rated conversation exchange "
                                            "could not be found."
                                        )
                                    record_feedback(
                                        interaction_id=interaction_id,
                                        grounding_rating=grounding_rating,
                                        helpfulness_rating=helpfulness_rating,
                                        **exchange,
                                    )
                                except Exception:
                                    logger.error(
                                        "XAIDA response feedback could not be saved."
                                    )
                                    st.error(
                                        "Feedback could not be saved. "
                                        "Please try again or contact the "
                                        "application administrator."
                                    )
                                else:
                                    message["feedback_submitted"] = True
                                    st.rerun()

    if session.metadata.pop("evaluation_storage_error", False):
        st.warning(
            "The Vertex AI response is available, but its evaluation metadata "
            "could not be saved. Notify the application administrator."
        )

    prompt = st.chat_input(
        "Ask the Vertex AI assistant...",
        key="xaida_chat_input",
    )

    if prompt:
        try:
            vertex_ai_assistant.chat(session, prompt)
            st.rerun()
        except Exception as error:
            logger.error(
                "XAIDA Vertex AI assistant request failed (%s).",
                type(error).__name__,
            )
            st.error(
                _chatbot_error_message(error)
            )
            if session.metadata.pop("evaluation_storage_error", False):
                st.warning(
                    "The request outcome could not be saved for evaluation. "
                    "Notify the application administrator."
                )


def close_completion_dialog():
    session.metadata["completion_dialog_dismissed"] = True


@st.dialog(
    "Audit completed",
    on_dismiss=close_completion_dialog,
)
def audit_completion_dialog():
    st.markdown(
        """
        <div class="xaida-completion-heading">
            <span class="xaida-completion-icon">✓</span>
            <div>
                <div class="xaida-completion-eyebrow">AUDIT CLOSED</div>
                <h2>Thank you for completing this audit.</h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(build_completion_summary(session))
    st.info(
        "The audit workflow and reporting are complete. You can continue "
        "reviewing this session's evidence with XAIDA, or close this dialog "
        "to return to the completed audit."
    )
    if st.button(
        "Return to completed audit",
        type="primary",
        use_container_width=True,
        key="close_audit_completion_dialog",
    ):
        close_completion_dialog()
        st.rerun()

stage = session.metadata.get("workflow_stage")
recommendation = None
recommendation_error = None
if stage != "audit_completion":
    next_step = get_next_recommended_step(session)
    recommendation = session.metadata.get("vertex_ai_recommendation")
    recommendation_stage = session.metadata.get(
        "vertex_ai_recommendation_stage"
    )
    recommendation_step = session.metadata.get(
        "vertex_ai_recommendation_step"
    )
    recommendation_state = f"{stage}:{next_step}"
    if (
        stage != "initialization"
        and (
            recommendation_stage != stage
            or recommendation_step != next_step
        )
        and session.metadata.get("vertex_ai_recommendation_attempt_state")
        != recommendation_state
    ):
        session.metadata["vertex_ai_recommendation_attempt_state"] = (
            recommendation_state
        )
        try:
            recommendation = vertex_ai_assistant.generate_recommendation(session)
            session.metadata["vertex_ai_recommendation"] = recommendation
            session.metadata["vertex_ai_recommendation_stage"] = stage
            session.metadata["vertex_ai_recommendation_step"] = next_step
            session.metadata.pop("vertex_ai_recommendation_error", None)
        except Exception:
            logger.exception("XAIDA recommendation generation failed.")
            session.metadata["vertex_ai_recommendation_error"] = (
                "Recommendation unavailable."
            )
            session.metadata["vertex_ai_recommendation_error_stage"] = stage
            session.metadata["vertex_ai_recommendation_error_step"] = next_step

    if (
        recommendation
        and session.metadata.get("vertex_ai_recommendation_stage") == stage
        and session.metadata.get("vertex_ai_recommendation_step") == next_step
    ):
        recommendation_error = None
    elif stage == "initialization":
        recommendation = (
            "Upload an audit dataset or choose a sample dataset to begin."
        )
    elif (
        session.metadata.get("vertex_ai_recommendation_error_stage") == stage
        and session.metadata.get("vertex_ai_recommendation_error_step")
        == next_step
    ):
        recommendation_error = (
            "Could not generate a Vertex AI recommendation: "
            f"{session.metadata['vertex_ai_recommendation_error']}\n\n"
            f"Next workflow action: {next_step}"
        )
    else:
        recommendation = None

render_action_notification(
    recommendation=recommendation,
    warning=recommendation_error,
)
if recommendation_error and st.button(
    "Retry Vertex AI recommendation",
    key="xaida_retry_vertex_ai_recommendation",
):
    session.metadata.pop("vertex_ai_recommendation_attempt_state", None)
    st.rerun()

# ============================================================
# SIDEBAR WIDTH
# ============================================================

st.markdown(
    """
    <style>

    section[data-testid="stSidebar"] {
        width: min(500px, 92vw) !important;
        max-width: min(500px, 92vw) !important;
    }

    div[data-testid="stDialog"]:has(.xaida-chat-intro) section[role="dialog"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        margin: 0 !important;
        background: #edf2f7 !important;
        color: #243244 !important;
        width: min(500px, 100vw) !important;
        max-width: min(500px, 100vw) !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        transform: none !important;
        border: 1px solid #d5dee8 !important;
        border-radius: 0 18px 18px 0 !important;
        box-shadow: 14px 0 36px rgba(31, 51, 73, 0.18) !important;
    }

    div[data-testid="stDialog"]:has(.xaida-chat-intro) section[role="dialog"] p,
    div[data-testid="stDialog"]:has(.xaida-chat-intro) section[role="dialog"] label,
    div[data-testid="stDialog"]:has(.xaida-chat-intro) section[role="dialog"] [data-testid="stMarkdownContainer"] {
        color: #243244 !important;
    }

    div[data-testid="stDialog"]:has(.xaida-chat-intro) section[role="dialog"] button[aria-label="Close"],
    div[data-testid="stDialog"]:has(.xaida-chat-intro) section[role="dialog"] button[aria-label="Close"] svg {
        color: #34495e !important;
        fill: #34495e !important;
    }

    div[data-testid="stDialog"]:has(.xaida-chat-intro) [data-testid="stChatMessage"] {
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.65rem;
        border: 1px solid #dce4ec;
        border-radius: 14px;
        background: #f8fafc;
    }

    div[data-testid="stDialog"]:has(.xaida-chat-intro) [data-testid="stChatInput"] {
        border-color: #cbd6e2;
        border-radius: 14px;
        background: #f8fafc;
    }

    .xaida-chat-intro {
        padding: 0.85rem 1rem 1rem;
        margin: 0 0 1rem;
        border: 1px solid #d6e0ea;
        border-radius: 14px;
        background: linear-gradient(135deg, #f8fafc, #e5edf5);
    }

    .xaida-chat-eyebrow, .xaida-completion-eyebrow {
        color: #62758a;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
    }

    .xaida-chat-title {
        margin-top: 0.2rem;
        color: #203449;
        font-size: 1.35rem;
        font-weight: 700;
    }

    .xaida-chat-subtitle {
        margin-top: 0.2rem;
        color: #526579;
        font-size: 0.9rem;
    }

    .xaida-completion-heading {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        padding: 1rem;
        margin: 0 0 1rem;
        border: 1px solid #d6e0ea;
        border-radius: 14px;
        background: linear-gradient(135deg, #f8fafc, #e5edf5);
    }

    .xaida-completion-icon {
        display: inline-flex;
        width: 2.5rem;
        height: 2.5rem;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: #d8e6e2;
        color: #315d53;
        font-size: 1.4rem;
        font-weight: 700;
    }

    .xaida-completion-heading h2 {
        margin: 0.15rem 0 0;
        color: #203449;
        font-size: 1.25rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("XAIDA", icon=":material/analytics:")
    st.caption("Explainable AI audit data analytics")
    auth_required = authentication_required()
    storage_enabled = session_storage_enabled()
    if auth_required:
        local_user_email = st.session_state.get("xaida_local_user_email")
        authenticated_user_email = st.user.get("email")
        signed_in_email = (
            local_user_email or authenticated_user_email or "unknown user"
        )
        st.caption(f"Signed in as {signed_in_email}")
    if auth_required or storage_enabled:
        exit_label = (
            "Log out and delete audit data"
            if auth_required and storage_enabled
            else "Exit and delete audit data"
            if storage_enabled
            else "Log out"
        )
        exit_help = (
            "Deletes stored audit data and logs you out."
            if auth_required and storage_enabled
            else "Deletes this audit session and its stored files."
            if storage_enabled
            else "Logs you out of XAIDA."
        )
        exit_col, new_analysis_col = st.columns(2)
        with exit_col:
            if st.button(
                exit_label,
                key="xaida_logout",
                width="stretch",
                help=exit_help,
            ):
                if auth_required and not storage_enabled:
                    if oidc_user_logged_in():
                        st.logout()
                    st.session_state.clear()
                    st.query_params.clear()
                    st.rerun()
                else:
                    queue_action_confirmation(
                        title=(
                            "Log out and delete audit data?"
                            if auth_required
                            else "Delete audit data?"
                        ),
                        message=(
                            "This permanently deletes the current audit "
                            "session and its stored files. Evaluation "
                            "records are retained."
                            + (
                                " You will also be logged out."
                                if auth_required
                                else ""
                            )
                        ),
                        confirm_label=exit_label,
                        action="logout_exit",
                        success_message=(
                            "You have been logged out and the audit data was "
                            "deleted."
                            if auth_required
                            else "The current audit data was deleted."
                        ),
                    )
                    st.rerun()
        with new_analysis_col:
            _render_new_analysis_button()
    else:
        _render_new_analysis_button()
    if storage_enabled:
        st.caption("Audit data is saved securely and expires after 24 hours of inactivity.")
# ============================================================
# XAIDA VERTEX AI ASSISTANT
# ============================================================

    if st.button(
        "XAIDA Vertex AI Assistant",
        key="xaida_chat_btn",
        type="primary",
        icon=":material/chat:",
        width="stretch",
    ):
        st.session_state["xaida_chat_open"] = True

    st.warning(
        "Privacy reminder: XAIDA sends relevant audit evidence to the "
        "organization-approved Vertex AI model when you ask questions. "
        "Use real audit data only if your organization has approved that "
        "service for it.",
        icon=":material/lock:",
    )

    with st.expander("About & feedback"):
        st.caption("Maintainer: XAIDA Project Team (anonymous)")
        st.write(
            "XAIDA is a prototype application that helps audit teams analyze data, "
            "recommends anomalies, validate and manage findings, and create reports."
        )
        st.write(
            "For deployment support, contact your organization's XAIDA "
            "administrator."
        )
        st.write("We welcome your feedback for the completion of the prototype" 
                 "acceptability evaluation requirements for a research study" 
                 "on the adoption of audit data analytics in external auditing."
                 "Please, complete the evaluation survey below.")
        st.info(
            "Survey responses are separate from audit findings, reports, "
            "and Vertex AI assistant evaluation records."
        )
        survey_url = (
            "https://forms.cloud.microsoft/Pages/ResponsePage.aspx?"
            "id=7ejkd1ByCUyx1a4xmBBBZy6uXT3TbvBNoqo8jp11bgxURERMNVNYWFMzRURMRExRU0FJMUo3VFFLRC4u"
            "&embed=true"
        )
        st.iframe(survey_url, width="stretch", height=480)
        st.link_button("Open survey in a new tab", survey_url)


# ===========================================
# ACTIONS
# ===========================================

    st.subheader("Available actions", icon=":material/bolt:")

    stage = session.metadata.get(
        "workflow_stage"
    )

    st.badge(
        str(stage or "unknown").replace("_", " ").title(),
        icon=":material/steps:",
        color="blue",
    )

    summary = (
        session.analysis.get(
            "analysis_dataset_summary",
            {}
        )
    )

    strategy = (
        summary.get(
            "strategy"
        )
        if summary
        else None
    )

# ===========================================
# DATASET UPLOAD
# ===========================================

    if (
        stage == "initialization"
        and not session.dataset.get("loaded", False)
    ):
        with st.container(border=True):
            st.markdown("**Add an audit dataset**")
            render_dataset_upload(session)

            sample_dataset = st.selectbox(
                "Or choose a sample dataset",
                [
                    "",
                    "Accounts Payable",
                    "Accounts Receivable",
                    "Budget Forecast",
                    "Expense Claims",
                    "General Ledger",
                ],
            )

            if sample_dataset and st.button(
                "Load sample dataset",
                type="primary",
                icon=":material/database:",
                width="stretch",
            ):
                load_sample_dataset(session, sample_dataset)
                queue_action_message(
                    "Sample dataset loaded",
                    f"{sample_dataset} is ready for data preparation.",
                    "success",
                )
                st.rerun()

    if (
        stage == "dataset"
        and session.dataset.get("loaded", False)
    ):

        if st.button(
            "Process Data Preparation",
            type="primary",
            use_container_width=True,
        ):
            _run_action_with_popup(
                "process_data_preparation",
                "Data preparation complete",
                "The dataset is ready for the next workflow step.",
            )

            st.rerun()


    if stage == "data_preparation":

        duplicate_count = (
            session.duplicates.get(
                "duplicate_count",
                0,
            )
        )

        if duplicate_count > 0:

            if st.button(
                "Proceed To Duplicate Review",
                type="primary",
                use_container_width=True,
            ):

                _run_action_with_popup(
                    "continue_to_duplicate_review",
                    "Duplicate review",
                    "Review the detected duplicate records.",
                )

                st.rerun()

        else:

            if st.button(
                "Proceed To Analysis",
                type="primary",
                use_container_width=True,
            ):

                _run_action_with_popup(
                    "continue_to_analysis",
                    "Ready for analysis",
                    "The dataset is ready for anomaly detection.",
                )

                st.rerun()
                    
    if stage == "duplicate_review":

        if strategy is None:

            if st.button(
                "Retain All Duplicates",
                use_container_width=True,
            ):
                _run_action_with_popup(
                    "retain_all_duplicates",
                    "Duplicate strategy saved",
                    "All duplicate records will be retained for analysis.",
                )

                st.session_state[
                       "active_tab"
                   ] = "Duplicate Review"
                
                st.rerun()

            if st.button(
                "Remove Duplicate Copies",
                use_container_width=True,
            ):
                _run_action_with_popup(
                    "remove_duplicate_copies",
                    "Duplicate strategy saved",
                    "Duplicate copies were removed from the analysis dataset.",
                )

                st.session_state[
                       "active_tab"
                   ] = "Duplicate Review"
                
                st.rerun()

            if st.button(
                "Manual Duplicate Review",
                use_container_width=True,
            ):
                _run_action_with_popup(
                    "manual_duplicate_review",
                    "Manual duplicate review",
                    "Select duplicate records to remove or retain.",
                )
                st.rerun()


        elif strategy == "manual_duplicate_review":

            selected_rows = (
                session.duplicates.get(
                    "selected_duplicate_count",
                    0,
                )
            )

            st.caption("Selected duplicate strategy: Manual Review")

            duplicate_review_complete = (
                session.duplicates.get(
                    "duplicate_review_complete",
                    False,
                )
            )

            if duplicate_review_complete:

                st.caption("Manual duplicate review is complete.")

                if st.button(
                    "Proceed To Analysis",
                    type="primary",
                    use_container_width=True,
                ):
                    _run_action_with_popup(
                        "continue_to_analysis",
                        "Ready for analysis",
                        "The dataset is ready for anomaly detection.",
                    )

                    st.session_state[
                        "active_tab"
                    ] = "Anomaly Detection"

                    st.rerun()

            if (
                st.session_state.get(ACTION_DIALOG_KEY, {}).get("action")
                != "remove_manual_duplicates"
                and
                not duplicate_review_complete
            ):       
                
                if st.button(
                    "Apply Manual Removal",
                    use_container_width=True,
                    disabled=(
                        selected_rows == 0
                        or
                        duplicate_review_complete
                    ),
                ):

                    st.session_state[
                        "pending_duplicate_rows"
                    ] = session.duplicates.get(
                        "selected_duplicate_rows",
                        [],
                    )

                    st.session_state[
                        "pending_duplicate_count"
                    ] = len(
                        st.session_state[
                            "pending_duplicate_rows"
                        ]
                    )
                    queue_action_confirmation(
                        title="Remove selected duplicates?",
                        message=(
                            "You are about to remove "
                            f"{st.session_state['pending_duplicate_count']} "
                            "selected records. This action cannot be undone."
                        ),
                        confirm_label="Confirm removal",
                        action="remove_manual_duplicates",
                        success_message=(
                            "The selected duplicate records were removed."
                        ),
                    )
                    st.rerun()

        elif strategy == "retain_first":

            st.caption("Selected duplicate strategy: Remove duplicate copies")

            if st.button(
                "Proceed To Analysis",
                type="primary",
                use_container_width=True,
            ):
                _run_action_with_popup(
                    "continue_to_analysis",
                    "Ready for analysis",
                    "The dataset is ready for anomaly detection.",
                )
                st.rerun()

        elif strategy == "retain_all":

            st.caption("Selected duplicate strategy: Retain all duplicates")

            if st.button(
                "Proceed To Analysis",
                type="primary",
                use_container_width=True,
            ):
                _run_action_with_popup(
                    "continue_to_analysis",
                    "Ready for analysis",
                    "The dataset is ready for anomaly detection.",
                )
                st.rerun()

    if stage == "analysis":

        if not session.analysis.get(
            "analysis_complete",
            False,
        ):

            if st.button(
                "Run Analysis",
                use_container_width=True,
                disabled=session.analysis.get(
                    "analysis_complete",
                    False,
                ),
            ):
                _run_action_with_popup(
                    "run_analysis",
                    "Analysis complete",
                    "Anomaly detection and explainability results are ready.",
                )

                st.rerun()
        else:

            if st.button(
                "Open Explainability",
                use_container_width=True,
            ):
                _run_action_with_popup(
                    "open_explainability",
                    "Explainability opened",
                    "Review the explanations for the flagged records.",
                )
                st.rerun()

    if stage == "explainability":

        if st.button(
            "Open Audit Review",
            use_container_width=True,
        ):
            _run_action_with_popup(
                "open_audit_review",
                "Audit review opened",
                "Review the enriched dataset and record your assessments.",
            )
            st.rerun()

    if stage == "audit_review":

        if (
            not session.review.get(
                "audit_review_complete",
                False,
            )
        ):
            
            # ==========================================
            # CONFIRM ALL FLAGGED RECORDS
            # ==========================================

            if st.button(
                "Confirm All Flagged Records",
                use_container_width=True,
                disabled=session.review.get(
                    "audit_review_complete",
                    False,
                ),
            ):
                queue_action_confirmation(
                    title="Confirm all flagged records?",
                    message=(
                        "All currently AI-flagged records will be classified "
                        "as Confirmed Anomaly. You can edit these assessments "
                        "until review decisions are saved."
                    ),
                    confirm_label="Confirm classifications",
                    action="confirm_all_flagged_records",
                    success_message=(
                        "AI-flagged records were classified as confirmed "
                        "anomalies. You may still update individual "
                        "assessments until review decisions are saved."
                    ),
                )
                st.rerun()

            # ==========================================
            # MANUAL REVIEW
            # ==========================================

            if st.button(
                "Manual Review",
                use_container_width=True,
                disabled=session.review.get(
                    "audit_review_complete",
                    False,
                ),
            ):
                queue_action_confirmation(
                    title="Enter manual review?",
                    message=(
                        "Manual Review lets you classify flagged records "
                        "individually using the assessment and comment fields."
                    ),
                    confirm_label="Enter manual review",
                    action="manual_review",
                    success_message="Manual review mode is enabled.",
                )
                st.rerun()

            # ==========================================
            # SAVE REVIEW DECISIONS
            # ==========================================
            
            review_df = (
                session.review.get(
                    "records"
                )
            )

            save_disabled = True
            remaining_reviews = 0

            if (
                review_df is not None
                and
                "Anomaly Flag" in review_df.columns
                and
                "Auditor Assessment" in review_df.columns
            ):

                remaining_reviews = len(
                    review_df[
                        (
                            review_df[
                                "Anomaly Flag"
                            ] == True
                        )
                        &
                        (
                            review_df[
                                "Auditor Assessment"
                            ]
                            .fillna("")
                            .astype(str)
                            .str.strip()
                            .eq("")
                        )
                    ]
                )

                if remaining_reviews > 0:

                    st.caption(
                        (
                            f"{remaining_reviews} records "
                            "still require auditor review. "
                            "All AI-flagged records must "
                            "be classified before findings "
                            "can be generated."
                        )
                    )

                else:

                    st.caption(
                        "All AI-flagged records reviewed. "
                        "Review decisions can now be saved."
                    )

                save_disabled = (
                    session.review.get(
                        "audit_review_complete",
                        False,
                    )
                    or
                    remaining_reviews > 0
                )

            if st.button(
                "Save Review Decisions",
                type="primary",
                use_container_width=True,
                disabled=save_disabled,
            ):
                queue_action_confirmation(
                    title="Save audit review?",
                    message=(
                        "Saving locks this review and creates a new dataset "
                        "version. You can then generate findings."
                    ),
                    confirm_label="Save review decisions",
                    action="save_review_decisions",
                    success_message="Review decisions were saved.",
                )
                st.rerun()

        # ==========================================
        # REVIEW COMPLETE STATUS
        # ==========================================

        if session.review.get(
            "audit_review_complete",
            False,
        ):

            st.caption(
                "Audit review is complete. The dataset is locked and the "
                "review version is recorded in Audit Trail and Dataset Lineage."
            )

            if session.review.get(
                "audit_review_complete",
                False,
            ):

                if st.button(
                    "Proceed To Findings",
                    type="primary",
                    use_container_width=True,
                ):

                    findings_result = execute_action(
                        "generate_findings",
                        session,
                    )

                    open_findings_result = execute_action(
                        "open_findings",
                        session,
                    )

                    st.session_state[
                        "active_tab"
                    ] = "Findings"
                    outcome = _action_outcome(
                        findings_result,
                        "Findings generated",
                        "Review the generated findings.",
                    )
                    if (
                        outcome["level"] == "success"
                        and (
                            not isinstance(open_findings_result, dict)
                            or not open_findings_result.get("success", False)
                        )
                    ):
                        outcome = _action_outcome(
                            open_findings_result,
                            "Findings could not be opened",
                            "Open the Findings tab to continue.",
                        )
                    queue_action_message(
                        outcome["title"],
                        outcome["message"],
                        outcome["level"],
                    )

                    st.rerun()

                
    if stage == "findings":

        if st.button(
            "Generate Report",
            use_container_width=True,
            type="primary",
        ):

            _run_action_with_popup(
                "generate_report",
                "Report generated",
                "The audit report is ready to download.",
            )

            st.rerun()

    if stage == "reporting":
        if st.button(
            "Complete Audit",
            type="primary",
            use_container_width=True,
        ):
            _run_action_with_popup(
                "complete_audit",
                "Audit completed",
                "The audit workflow and reporting are complete.",
            )
            st.rerun()

    if stage == "audit_completion":
        st.info(
            "The audit is closed. Review the completion summary and continue "
            "to the completed audit when ready."
        )


# ============================================================
# MAIN WORKSPACE
# ============================================================

completion_dialog_pending = (
    session.metadata.get("workflow_stage") == "audit_completion"
    and not session.metadata.get("completion_dialog_dismissed", False)
)
action_notification = st.session_state.get(ACTION_DIALOG_KEY)
action_dialog_pending = bool(
    action_notification
    and action_notification.get("mode") == "confirmation"
)
if action_dialog_pending:
    render_action_dialog(_handle_action_confirmation)
elif (
    st.session_state["xaida_chat_open"]
    and not completion_dialog_pending
):
    xaida_chat_dialog()

st.markdown(
    '<div class="right-panel">',
    unsafe_allow_html=True,
)

render_evidence_panel(
    session,
    vertex_ai_assistant,
)

if (
    not action_dialog_pending
    and
    session.metadata.get("workflow_stage") == "audit_completion"
    and not session.metadata.get("completion_dialog_dismissed", False)
):
    audit_completion_dialog()

st.markdown(
   "</div>",
    unsafe_allow_html=True,
)

if session_storage_enabled():
    try:
        save_session()
    except SessionPersistenceError as error:
        logger.error("XAIDA audit session could not be saved.")
        st.error(str(error))
        st.stop()
