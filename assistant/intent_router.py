# assistant/intent_router.py

from dataclasses import dataclass


# ============================================================
# INTENT RESULT
# ============================================================

@dataclass
class IntentResult:
    intent: str
    confidence: float
    parameters: dict


# ============================================================
# INTENT ROUTER
# ============================================================

class IntentRouter:

    def route(
        self,
        user_message: str,
    ) -> IntentResult:

        message = (
            user_message
            .lower()
            .strip()
        )

        # ====================================================
        # DATASET
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "dataset schema",
                "show schema",
                "column names",
                "dataset structure",
                "dataset preview",
            ]
        ):
            return IntentResult(
                intent="dataset_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # DATA PREPARATION
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "missing values",
                "null values",
                "data quality",
                "imputation",
            ]
        ):
            return IntentResult(
                intent="data_preparation_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # DUPLICATE REVIEW ACTIONS
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "retain all duplicates",
                "keep all duplicates",
            ]
        ):
            return IntentResult(
                intent="retain_all_duplicates",
                confidence=1.0,
                parameters={},
            )

        if any(
            phrase in message
            for phrase in [
                "drop all duplicates",
                "remove all duplicates",
            ]
        ):
            return IntentResult(
                intent="drop_all_duplicates",
                confidence=1.0,
                parameters={},
            )

        if any(
            phrase in message
            for phrase in [
                "review duplicates",
                "duplicate review",
                "duplicate groups",
            ]
        ):
            return IntentResult(
                intent="duplicate_review_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # ANALYSIS
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "run analysis",
                "start analysis",
            ]
        ):
            return IntentResult(
                intent="run_analysis",
                confidence=1.0,
                parameters={},
            )

        if any(
            phrase in message
            for phrase in [
                "risk score",
                "risk scores",
                "risk level",
                "anomaly",
                "anomalies",
                "flagged transactions",
                "high risk transactions",
                "flag rate",
            ]
        ):
            return IntentResult(
                intent="analysis_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # EXPLAINABILITY
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "show explainability",
                "explain anomalies",
                "why was this flagged",
                "why flagged",
                "why was this transaction flagged",
                "risk driver",
                "risk drivers",
                "feature driver",
                "feature drivers",
                "shap",
                "shap values",
                "transaction explanation",
                "explain this transaction",
                "what caused this score",
            ]
        ):
            return IntentResult(
                intent="explainability_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # AUDIT REVIEW
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "audit review",
                "review findings",
                "false positive",
                "confirmed anomaly",
                "requires investigation",
                "potential finding",
            ]
        ):
            return IntentResult(
                intent="audit_review_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # FINDINGS
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "show findings",
                "open findings",
                "validated findings",
                "finding status",
            ]
        ):
            return IntentResult(
                intent="findings_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # REPORTING
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "generate report",
                "export report",
                "pdf report",
                "excel report",
            ]
        ):
            return IntentResult(
                intent="reporting_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # WORKFLOW / NARRATIVE
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "executive summary",
                "audit summary",
                "audit overview",
                "audit narrative",
                "audit recap",
                "audit retrospective",
                "walk me through the audit",
                "summarise this audit",
                "summarize this audit",
                "what happened",
                "workflow summary",
            ]
        ):
            return IntentResult(
                intent="workflow_summary",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # LINEAGE
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "dataset lineage",
                "lineage",
                "dataset version",
                "version history",
                "dataset evolution",
                "change history",
            ]
        ):
            return IntentResult(
                intent="lineage_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # AUDIT TRAIL
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "audit trail",
                "audit log",
                "workflow history",
                "audit history",
                "recent audit events",
            ]
        ):
            return IntentResult(
                intent="audit_trail_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # WORKFLOW GUIDANCE
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "next step",
                "next workflow step",
                "what should i do next",
                "workflow recommendation",
                "workflow status",
                "audit readiness",
            ]
        ):
            return IntentResult(
                intent="workflow_guidance",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # FALLBACK
        # ====================================================

        return IntentResult(
            intent="audit_inquiry",
            confidence=0.5,
            parameters={},
        )