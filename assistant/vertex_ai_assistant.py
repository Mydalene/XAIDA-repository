# assistant/vertex_ai_assistant.py

import json
import logging
import time
import uuid

from assistant.context.context_builder import (
    build_context,
)
from assistant.context_prioritizer import (
    build_prioritized_context,
)
from assistant.context_router import (
    classify_question,
)
from assistant.conversation_manager import (
    add_assistant_message,
    add_user_message,
    get_recent_history,
)
from assistant.evaluation_store import record_interaction
from assistant.inquiry_router import (
    route_inquiry,
)
from assistant.output_validator import (
    validate_response,
)
from assistant.prompts import (
    build_system_messages,
)
from assistant.response_guard import (
    verify_context,
)
from assistant.session_validator import (
    validate_session,
)
from core.vertex_ai_client import (
    create_client,
)

logger = logging.getLogger(__name__)

class XaidaVertexAIAssistant:

    def __init__(self):

        self.client = None

    def _get_completion_client(self):
        if self.client is None:
            self.client = create_client()
        return self.client

    def chat(
        self,
        session,
        user_message,
    ):
        interaction_id = str(uuid.uuid4())
        response_category = classify_question(user_message)
        workflow_stage = session.metadata.get(
            "workflow_stage",
            "unknown",
        )
        started_at = time.perf_counter()

        try:
            response = self._chat(session, user_message)
        except Exception as error:
            self._record_evaluation_event(
                session=session,
                interaction_id=interaction_id,
                workflow_stage=workflow_stage,
                response_category=response_category,
                started_at=started_at,
                outcome="error",
                error_category=self._error_category(error),
            )
            raise

        outcome = "success"
        error_category = None
        if response.startswith("Session validation failed:"):
            outcome = "error"
            error_category = "session_validation_error"

        if (
            outcome == "success"
            and session.conversation
            and session.conversation[-1]["role"] == "assistant"
        ):
            session.conversation[-1]["interaction_id"] = interaction_id

        self._record_evaluation_event(
            session=session,
            interaction_id=interaction_id,
            workflow_stage=workflow_stage,
            response_category=response_category,
            started_at=started_at,
            outcome=outcome,
            error_category=error_category,
        )
        return response

    @staticmethod
    def _error_category(error):
        error_type = type(error).__name__
        if error_type in {
            "APIConnectionError",
            "APITimeoutError",
            "RateLimitError",
            "ServiceUnavailable",
            "DeadlineExceeded",
            "ResourceExhausted",
        }:
            return "ai_service_unavailable"
        if error_type in {
            "AuthenticationError",
            "PermissionDeniedError",
            "Unauthenticated",
            "PermissionDenied",
            "NotFound",
            "InvalidArgument",
        }:
            return "ai_service_configuration"
        if isinstance(error, RuntimeError):
            return "ai_service_configuration"
        return "unexpected_error"

    @staticmethod
    def _record_evaluation_event(
        *,
        session,
        interaction_id,
        workflow_stage,
        response_category,
        started_at,
        outcome,
        error_category,
    ):
        try:
            record_interaction(
                interaction_id=interaction_id,
                evaluation_session_id=session.evaluation_session_id,
                workflow_stage=workflow_stage,
                response_category=response_category,
                latency_ms=max(
                    0,
                    round((time.perf_counter() - started_at) * 1000),
                ),
                outcome=outcome,
                error_category=error_category,
            )
        except Exception:
            logger.error("XAIDA evaluation metadata could not be saved.")
            session.metadata["evaluation_storage_error"] = True

    def _chat(
        self,
        session,
        user_message,
    ):

        valid_session, errors = (
            validate_session(
                session
            )
        )

        if not valid_session:

            error_message = (
                "Session validation failed:\n\n"
                + "\n".join(
                    f"• {error}"
                    for error in errors
                )
            )

            add_user_message(
                session,
                user_message,
            )

            add_assistant_message(
                session,
                error_message,
            )

            return error_message

        full_context = build_context(
            session,
            user_message=user_message,
        )

        question_type = classify_question(
            user_message
        )

        inquiry_result = route_inquiry(
            user_message
        )
        full_context[
            "user_inquiry"
        ] = (
            inquiry_result.inquiry
        )

        full_context[
            "inquiry_confidence"
        ] = (
            inquiry_result.confidence
        )
        full_context[
            "question_category"
        ] = question_type

        prioritized_context = (
            build_prioritized_context(
                full_context=full_context,
                categories=[question_type],
            )
        )

# ==================================================
# FLATTEN PRIORITIZED CONTEXT
# ==================================================

        prompt_context = {}

        prompt_context.update(
            prioritized_context["secondary_evidence"]
        )

        prompt_context.update(
            prioritized_context["primary_evidence"]
        )
        prompt_context["question_category"] = question_type

# ==================================================
# CONTEXT VALIDATION
# ==================================================

        is_valid, guard_message = (
            verify_context(
                question_type,
                prompt_context,
            )
        )

        if not is_valid:

            add_user_message(
                session,
                user_message,
            )

            add_assistant_message(
                session,
                guard_message,
            )

            return guard_message

        messages = build_system_messages(
            prompt_context
        )

        messages.extend(
            get_recent_history(
                session
            )
        )

        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        try:

            assistant_message = (
                self._get_completion_client().generate_content(messages)
            )

        except Exception:
            raise

        add_user_message(
            session,
            user_message,
        )

        valid, validated_response = (
            validate_response(
                assistant_message
            )
        )

        assistant_message = (
            validated_response
        )

        add_assistant_message(
            session,
            assistant_message,
        )

        return assistant_message

    def generate_recommendation(
        self,
        session,
    ):
        context = build_context(session)
        evidence = {
            key: context.get(key)
            for key in (
                "workflow_stage",
                "next_recommended_step",
                "audit_readiness_score",
                "audit_readiness_status",
                "analysis_complete",
                "flagged_transaction_count",
                "high_risk_transaction_count",
                "explainability_coverage",
                "remaining_reviews",
                "audit_review_complete",
                "open_findings",
                "validated_findings",
                "report_generated",
            )
            if key in context
        }

        recommendation = self._get_completion_client().generate_content(
            [
                {
                    "role": "system",
                    "content": (
                        "You are XAIDA's Vertex AI workflow recommendation "
                        "assistant. "
                        "Return one short, actionable next step followed "
                        "by one brief sentence explaining what that process "
                        "does or why it comes next. Use only the supplied "
                        "audit status. Treat next_recommended_step as the "
                        "authoritative next process unless the other supplied "
                        "status clearly shows it is blocked. Do not include "
                        "summaries, audit conclusions, uncertainty statements, "
                        "or any extra recommendations."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Recommend the next action and briefly explain the "
                        "process using only this audit status:\n"
                        f"{json.dumps(evidence, sort_keys=True)}"
                    ),
                },
            ],
        )
        recommendation = recommendation.strip()
        if not recommendation:
            raise ValueError(
                "Vertex AI returned an empty recommendation."
            )
        return recommendation

    def generate_finding_recommendations(
        self,
        session,
    ):
        findings_df = session.findings.get(
            "findings_dataframe"
        )
        if findings_df is None:
            raise ValueError(
                "Generate findings before requesting follow-up recommendations."
            )

        evidence_columns = [
            column
            for column in (
                "Finding ID",
                "Risk Score",
                "Severity",
                "Auditor Assessment",
                "Finding Status",
                "Source Dataset Version",
            )
            if column in findings_df.columns
        ]
        findings = (
            findings_df[evidence_columns]
            .head(20)
            .to_dict("records")
        )
        change_history = [
            {
                "version": change.get("version"),
                "stage": change.get("stage"),
                "action": change.get("action"),
            }
            for change in session.analysis.get(
                "dataset_change_log",
                [],
            )
        ]
        evidence = {
            "workflow_stage": session.metadata.get(
                "workflow_stage"
            ),
            "source_dataset_version": session.findings.get(
                "source_dataset_version"
            ),
            "finding_count": len(findings_df),
            "findings": findings,
            "dataset_changes": change_history,
        }
        recommendations = self._get_completion_client().generate_content(
            [
                {
                    "role": "system",
                    "content": (
                        "You are XAIDA, an audit evidence assistant powered "
                        "by Vertex AI. "
                        "Suggest concise audit follow-up procedures grounded "
                        "only in the supplied finding evidence. Do not assume "
                        "fraud, error, or control failure; do not make audit "
                        "conclusions. State when evidence is insufficient."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Prepare up to three specific, actionable follow-up "
                        f"recommendations from this evidence:\n{evidence}"
                    ),
                },
            ],
        )
        recommendations = recommendations.strip()
        if not recommendations:
            raise ValueError(
                "Vertex AI returned no follow-up recommendations."
            )
        return recommendations