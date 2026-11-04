# ===================================
# AUDIT REVIEW
# ===================================

def build_audit_review_context(
    session,
    risk_summary=None,
):

    review_df = (
        session.review.get(
            "records"
        )
    )

    total_records = 0
    ai_flagged_records = 0
    auditor_identified_records = 0
    unassessed_records = 0

    confirmed_anomalies = 0
    potential_findings = 0
    false_positives = 0
    requires_investigation = 0

    if review_df is not None:

        total_records = len(
            review_df
        )

        if (
            "Anomaly Flag"
            in review_df.columns
        ):
            ai_flagged_records = int(
                review_df[
                    "Anomaly Flag"
                ].sum()
            )

        if (
            "Auditor Assessment"
            in review_df.columns
        ):

            assessment_col = (
                "Auditor Assessment"
            )

            confirmed_anomalies = int(
                review_df[
                    assessment_col
                ]
                .eq(
                    "Confirmed Anomaly"
                )
                .sum()
            )

            potential_findings = int(
                review_df[
                    assessment_col
                ]
                .eq(
                    "Potential Finding"
                )
                .sum()
            )

            false_positives = int(
                review_df[
                    assessment_col
                ]
                .eq(
                    "False Positive"
                )
                .sum()
            )

            requires_investigation = int(
                review_df[
                    assessment_col
                ]
                .eq(
                    "Requires Investigation"
                )
                .sum()
            )

            if (
                "Anomaly Flag"
                in review_df.columns
            ):

                auditor_identified_records = len(
                    review_df[
                        (
                            review_df[
                                "Anomaly Flag"
                            ]
                            == False
                        )
                        &
                        (
                            review_df[
                                "Auditor Assessment"
                            ]
                            .isin(
                                [
                                    "Confirmed Anomaly",
                                    "Potential Finding",
                                    "Requires Investigation",
                                ]
                            )
                        )
                    ]
                )

                unassessed_records = len(
                    review_df[
                        (
                            review_df[
                                "Anomaly Flag"
                            ]
                            == False
                        )
                        &
                        (
                            review_df[
                                "Auditor Assessment"
                            ]
                            .isna()
                        )
                    ]
                )

    review_records = (
        review_df.head(50).to_dict("records")
        if review_df is not None
        else []
    )

    remaining_reviews = (
        session.review.get(
            "remaining_reviews",
            0,
        )
    )

    audit_review_complete = (
        session.review.get(
            "audit_review_complete",
            False,
        )
    )

    return {

        # ===================================
        # REVIEW STATUS
        # ===================================

        "audit_review_complete":
        audit_review_complete,

        "manual_review_mode":
        (
            session.review.get(
                "manual_review_mode",
                False,
            )
        ),

        "review_mode":
        (
            session.review.get(
                "mode"
            )
        ),

        "review_summary":
        (
            session.review.get(
                "summary",
                {},
            )
        ),

        "remaining_reviews":
        remaining_reviews,

        # ===================================
        # REVIEW DATASET METRICS
        # ===================================

        "review_record_count":
        total_records,

        "audit_review_records":
            review_records,

        "audit_review_records_included":
            len(review_records),

        "ai_flagged_records":
        ai_flagged_records,

        "auditor_identified_records":
        auditor_identified_records,

        "unassessed_records":
        unassessed_records,

        # ===================================
        # REVIEW CLASSIFICATIONS
        # ===================================

        "confirmed_anomaly_count":
        confirmed_anomalies,

        "potential_finding_count":
        potential_findings,

        "false_positive_count":
        false_positives,

        "requires_investigation_count":
        requires_investigation,

        # ===================================
        # AUDITOR OPTIONS
        # ===================================

        "auditor_assessment_options":
        [
            "Confirmed Anomaly",
            "Potential Finding",
            "False Positive",
            "Requires Investigation",
        ],

        # ===================================
        # ANALYSIS CLOSURE STATUS
        # ===================================

        "analysis_complete":
        (
            session.analysis.get(
                "analysis_complete",
                False,
            )
        ),

        "analysis_closed":
        audit_review_complete,

        "dataset_locked":
        audit_review_complete,

        "findings_available":
        audit_review_complete,

        # ===================================
        # REVIEW NAVIGATION
        # ===================================

        "audit_review_sections":
        [
            "Latest Dataset Version",
            "Audit Review Metrics",
            "Review Classification",
            "Auditor Assessment",
            "Auditor Comment",
        ],

        "audit_review_tab_name":
            "Audit Review",

        "audit_review_tab_location":
            "Evidence stages tabs in the main Audit Evidence panel.",

        "audit_review_workflow_steps":
        [
            "Review AI-Flagged Records",
            "Review Auditor-Identified Records",
            "Classify Flagged Transactions",
            "Add Auditor Comments",
            "Resolve Remaining Reviews",
            "Save Review Decisions",
            "Proceed To Findings",
        ],

        "audit_review_navigation_help":
        """
        1. Review AI-Flagged Records

        2. Review Auditor-Identified Records

        3. Assign Auditor Assessment

        4. Add Auditor Comment

        5. Resolve Remaining Reviews

        6. Save Review Decisions

        7. Proceed To Findings
        """,

        # ===================================
        # FINDINGS READINESS
        # ===================================

        "can_generate_findings":
        (
            audit_review_complete
            and
            remaining_reviews == 0
        ),
    }