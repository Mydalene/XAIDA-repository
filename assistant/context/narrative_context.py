def build_narrative_context(
    session,
    risk_summary,
):

    findings_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    total_findings = (
        len(findings_df)
        if findings_df is not None
        else 0
    )

    return {

        # ===================================
        # EXECUTIVE SUMMARY
        # ===================================

        "audit_workflow_summary": {

            "audit_name":
                session.metadata.get(
                    "audit_name"
                ),

            "workflow_stage":
                session.metadata.get(
                    "workflow_stage"
                ),


            "records_loaded":
                session.dataset.get(
                    "rows",
                    0,
                ),

            "duplicates_detected":
                session.duplicates.get(
                    "duplicate_count",
                    0,
                ),

            "flagged_transactions":
                risk_summary.get(
                    "flagged_transactions",
                    0,
                ),

            "risk_level":
                risk_summary.get(
                    "risk_level"
                ),

            "total_findings":
                total_findings,

            "validated_findings":
                len(
                    session.findings.get(
                        "validated",
                        [],
                    )
                ),

            "open_findings":
                len(
                    session.findings.get(
                        "open",
                        [],
                    )
                ),

            "dataset_versions":
                len(
                    session.analysis.get(
                        "dataset_version_metadata",
                        {}
                    )
                ),

            "audit_events":
                len(
                    session.audit_log
                ),
        },

        # ===================================
        # READINESS
        # ===================================

        "audit_readiness_score":
            session.metadata.get(
                "audit_readiness_score"
            ),

        "audit_readiness_status":
            session.metadata.get(
                "audit_readiness_status"
            ),

        "audit_ready":
            session.metadata.get(
                "audit_ready"
            ),

        # ===================================
        # WORKFLOW
        # ===================================

        "workflow_stage":
            session.metadata.get(
                "workflow_stage"
            ),


        # ===================================
        # TIMELINE
        # ===================================

        "audit_timeline": [
            {
                "action":
                    event.get(
                        "action"
                    ),

                "stage":
                    event.get(
                        "stage"
                    ),

                "details":
                    event.get(
                        "details"
                    ),
            }
            for event
            in session.audit_log
        ],

        # ===================================
        # LINEAGE
        # ===================================

        "dataset_lineage_summary": [
            {
                "version":
                    version,

                "stage":
                    metadata.get(
                        "stage"
                    ),

                "action":
                    metadata.get(
                        "action"
                    ),
            }
            for version, metadata
            in session.analysis.get(
                "dataset_version_metadata",
                {},
            ).items()
        ],

        # ===================================
        # REVIEW SUMMARY
        # ===================================

        "review_summary": {

            "confirmed_anomaly_count":
                session.review.get(
                    "confirmed_anomaly_count",
                    0,
                ),

            "potential_finding_count":
                session.review.get(
                    "potential_finding_count",
                    0,
                ),

            "false_positive_count":
                session.review.get(
                    "false_positive_count",
                    0,
                ),

            "requires_investigation_count":
                session.review.get(
                    "requires_investigation_count",
                    0,
                ),
        },

        # ===================================
        # REPORTING STATUS
        # ===================================

        "report_generated":
            session.analysis.get(
                "report_generated",
                False,
            ),

        # ===================================
        # NARRATIVE NAVIGATION
        # ===================================

        "narrative_sections": [
            "Audit Overview",
            "Data Preparation",
            "Duplicate Review",
            "Analysis",
            "Explainability",
            "Audit Review",
            "Findings",
            "Reporting",
        ],
    }