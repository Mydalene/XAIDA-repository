from findings.finding_status import summarize_finding_status


# ===================================
# FINDINGS
# ===================================

def build_findings_context(
    session,
):

    findings_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    fallback_findings = {
        "Open": session.findings.get("open", []),
        "Under Review": session.findings.get("under_review", []),
        "Validated": session.findings.get("validated", []),
        "Resolved": session.findings.get("resolved", []),
        "Dismissed": session.findings.get("dismissed", []),
    }
    status_summaries = {
        status: summarize_finding_status(
            findings_df,
            status,
            records,
        )
        for status, records in fallback_findings.items()
    }
    status_counts = {
        status: summary[0]
        for status, summary in status_summaries.items()
    }
    open_findings = status_counts["Open"]
    under_review_findings = status_counts["Under Review"]
    validated_findings = status_counts["Validated"]
    resolved_findings = status_counts["Resolved"]
    dismissed_findings = status_counts["Dismissed"]

    findings_locked = (
        session.findings.get(
            "findings_locked",
            False,
        )
    )
    workflow_stage = session.metadata.get("workflow_stage")

    return {

        # ==============================
        # FINDING METRICS
        # ==============================

        "total_findings":
        (
            open_findings
            + under_review_findings
            + validated_findings
            + resolved_findings
            + dismissed_findings
        ),

        "open_findings":
            open_findings,

        "under_review_findings":
            under_review_findings,

        "validated_findings":
            validated_findings,

        "resolved_findings":
            resolved_findings,

        "dismissed_findings":
            dismissed_findings,

        # ==============================
        # FINDING STATUS
        # ==============================

        "findings_available":
        (
            findings_df is not None
            and len(findings_df) > 0
        ),

        "findings_locked":
            findings_locked,

        "findings_dataset_version":
            session.findings.get("findings_dataset_version"),

        "findings_source_dataset_version":
            session.findings.get("source_dataset_version"),

        "can_generate_report":
            workflow_stage == "findings" and not findings_locked,

        "severity_assignment_methodology":
            "Generated findings inherit the analysis population risk level: "
            "Low maps to Low, Moderate maps to Medium, and High maps to High. "
            "Analysis classifies population risk as Low below 2% anomaly rate, "
            "Moderate from 2% to below 5%, and High at 5% or above. The mapping "
            "is applied uniformly to generated findings; auditors can edit "
            "severity in the Findings register. Critical is not produced by "
            "this analysis risk-level mapping.",

        # ==============================
        # FINDING REGISTER
        # ==============================

        "findings_register":
        (
            findings_df
            .head(50)
            .to_dict("records")
            if findings_df is not None
            else []
        ),

        # ==============================
        # FINDING DETAILS
        # ==============================

        "validated_finding_details":
            status_summaries["Validated"][1],

        "open_finding_details":
            status_summaries["Open"][1],

        # ==============================
        # SOURCE FINDINGS
        # ==============================

        "anomaly_findings":
        (
            session.analysis.get(
                "anomaly_findings",
                "",
            )
        ),

        "explainability_findings":
        (
            session.analysis.get(
                "explainability_findings",
                "",
            )
        ),

        # ==============================
        # NAVIGATION
        # ==============================

        "findings_sections":
        [
            "Findings Metrics",
            "Findings Register",
            "Finding Details",
            "Auditor Comment",
            "Management Response",
            "Source Record",
        ],

        "findings_workflow_steps":
        [
            "Review Findings Register",
            "Review Finding Details",
            "Review Auditor Comments",
            "Review Management Responses",
            "Validate Findings",
            "Resolve Findings",
            "Proceed To Reporting",
        ],
    }