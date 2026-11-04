# ============================================================
# XAIDA 5.3
# assistant/inquiry_router.py
# ============================================================

from dataclasses import dataclass


# ============================================================
# RESULT
# ============================================================

@dataclass
class InquiryResult:

    inquiry: str
    confidence: float
    parameters: dict


# ============================================================
# INQUIRY ROUTER
# ============================================================

class InquiryRouter:

    def route(
        self,
        user_message: str,
    ) -> InquiryResult:

        message = (
            user_message
            .lower()
            .strip()
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
                "audit recap",
                "audit narrative",
                "audit retrospective",
                "walk me through the audit",
                "summarise this audit",
                "summarize this audit",
                "what happened",
                "workflow summary",
            ]
        ):
            return InquiryResult(
                inquiry="workflow_summary",
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
            return InquiryResult(
                inquiry="workflow_guidance",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # DATASET
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "dataset schema",
                "show schema",
                "columns",
                "dataset preview",
                "dataset structure",
            ]
        ):
            return InquiryResult(
                inquiry="dataset_inquiry",
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
            return InquiryResult(
                inquiry="data_preparation_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # DUPLICATE REVIEW
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "duplicate review",
                "duplicate groups",
                "duplicate records",
                "duplicate strategy",
            ]
        ):
            return InquiryResult(
                inquiry="duplicate_review_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # ANALYSIS
        # ====================================================

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
                "analysis results",
            ]
        ):
            return InquiryResult(
                inquiry="analysis_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # EXPLAINABILITY
        # ====================================================

        if any(
            phrase in message
            for phrase in [
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
                "show explainability",
                "explain anomalies",
            ]
        ):
            return InquiryResult(
                inquiry="explainability_inquiry",
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
                "auditor assessment",
                "false positive",
                "confirmed anomaly",
                "requires investigation",
                "potential finding",
            ]
        ):
            return InquiryResult(
                inquiry="audit_review_inquiry",
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
            return InquiryResult(
                inquiry="findings_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # REPORTING
        # ====================================================

        if any(
            phrase in message
            for phrase in [
                "report",
                "reporting",
                "audit report",
                "pdf report",
                "excel report",
            ]
        ):
            return InquiryResult(
                inquiry="reporting_inquiry",
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
                "version history",
                "dataset version",
                "dataset evolution",
                "change history",
            ]
        ):
            return InquiryResult(
                inquiry="lineage_inquiry",
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
                "audit history",
                "workflow history",
                "recent audit events",
            ]
        ):
            return InquiryResult(
                inquiry="audit_trail_inquiry",
                confidence=1.0,
                parameters={},
            )

        # ====================================================
        # DEFAULT
        # ====================================================

        return InquiryResult(
            inquiry="general_inquiry",
            confidence=0.5,
            parameters={},
        )


# ============================================================
# SINGLETON
# ============================================================

router = InquiryRouter()


def route_inquiry(
    user_message: str,
) -> InquiryResult:

    return router.route(
        user_message
    )
