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

    open_findings = 0
    under_review_findings = 0
    validated_findings = 0
    resolved_findings = 0
    dismissed_findings = 0

    if (
        findings_df is not None
        and
        len(findings_df) > 0
    ):

        open_findings = int(
            findings_df[
                "Finding Status"
            ]
            .eq("Open")
            .sum()
        )

        under_review_findings = int(
            findings_df[
                "Finding Status"
            ]
            .eq("Under Review")
            .sum()
        )

        validated_findings = int(
            findings_df[
                "Finding Status"
            ]
            .eq("Validated")
            .sum()
        )

        resolved_findings = int(
            findings_df[
                "Finding Status"
            ]
            .eq("Resolved")
            .sum()
        )

        dismissed_findings = int(
            findings_df[
                "Finding Status"
            ]
            .eq("Dismissed")
            .sum()
        )

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
            "New findings are initialized as Medium by default in XAIDA. "
            "This is a software default, not a severity scoring rubric or "
            "evidence-based severity rationale. The auditor can edit severity "
            "in the Findings register; no documented rule maps evidence to "
            "Low, Medium, High, or Critical.",

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
        (
            session.findings.get(
                "validated",
                [],
            )
        ),

        "open_finding_details":
        (
            session.findings.get(
                "open",
                [],
            )
        ),

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