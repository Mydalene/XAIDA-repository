# ============================================================
# XAIDA
# exports/report_generator.py
# ============================================================

from datetime import datetime

import pandas as pd
import streamlit as st

from assistant.session_manager import (
    get_session,
)

# ============================================================
# REPORT ELIGIBILITY
# ============================================================

def report_generation_allowed():

    session = get_session()

    return bool(
        session.reporting.get(
            "pdf_ready",
            False,
        )
    )

# ============================================================
# TIMESTAMP
# ============================================================

def build_timestamp():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

# ============================================================
# DATASET SUMMARY
# ============================================================

def build_dataset_summary():

    session = get_session()

    dataframe = (
        session.dataset.get(
            "dataframe"
        )
    )

    return {

        "dataset_name":
            session.dataset.get(
                "dataset_name",
                "Dataset",
            ),

        "records":
            len(dataframe)
            if dataframe is not None
            else 0,

        "columns":
            len(dataframe.columns)
            if dataframe is not None
            else 0,

        "workflow_stage":
            session.metadata.get(
                "workflow_stage"
            ),
    }

# ============================================================
# REVIEW DATASET
# ============================================================

def build_review_dataset():

    session = get_session()

    review_df = (
        session.review.get(
            "records"
        )
    )

    if review_df is None:

        return pd.DataFrame()

    return review_df.copy()

# ============================================================
# DATA PREPARATION
# ============================================================

def build_data_preparation_summary():

    session = get_session()

    return {

        "strategy":
            session.analysis.get(
                "strategy",
                "-"
            ),

        "missing_before":
            session.analysis.get(
                "missing_before",
                0
            ),

        "missing_after":
            session.analysis.get(
                "missing_after",
                0
            ),

        "columns_modified":
            session.analysis.get(
                "columns_modified",
                []
            ),
    }

# ============================================================
# DUPLICATE REVIEW
# ============================================================

def build_duplicate_review_summary():

    session = get_session()

    return {

        "duplicate_count":
            session.duplicates.get(
                "duplicate_count",
                0,
            ),

        "duplicate_groups":
            session.duplicates.get(
                "duplicate_groups",
                0,
            ),

        "strategy":
            session.duplicates.get(
                "strategy",
                "-",
            ),

        "records_removed":
            session.duplicates.get(
                "records_removed",
                0,
            ),
    }

# ============================================================
# ANALYSIS SUMMARY
# ============================================================

def build_analysis_summary():

    session = get_session()

    risk_summary = (
        session.analysis.get(
            "risk_summary",
            {},
        )
    )

    review_df = (
        session.review.get(
            "records"
        )
    )

    total_records = (
        len(review_df)
        if review_df is not None
        else 0
    )

    return {

        "records_analysed":
            total_records,

        "flagged_records":
            risk_summary.get(
                "flagged_transactions",
                0,
            ),

        "anomaly_rate":
            risk_summary.get(
                "anomaly_rate",
                0,
            ),

        "risk_level":
            risk_summary.get(
                "risk_level",
                "-",
            ),
    }

# ============================================================
# EXPLAINABILITY SUMMARY
# ============================================================

def build_explainability_summary():

    session = get_session()

    top_features = (
        session.explainability.get(
            "top_features"
        )
    )

    if top_features is None:

        return []

    return (
        top_features
        .head(10)
        .to_dict(
            orient="records"
        )
    )


# ============================================================
# FINDINGS REGISTER
# ============================================================

def build_findings_register():

    session = get_session()

    findings_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    if findings_df is None:

        return pd.DataFrame()

    return findings_df.copy()

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================

def build_executive_summary():

    session = get_session()

    review_df = (
        build_review_dataset()
    )

    findings_df = (
        build_findings_register()
    )

    confirmed = 0
    potential = 0
    investigation = 0
    false_positive = 0
    auditor_identified = 0

    if not findings_df.empty:

        confirmed = int(
            findings_df[
                "Auditor Assessment"
            ]
            .eq(
                "Confirmed Anomaly"
            )
            .sum()
        )

        potential = int(
            findings_df[
                "Auditor Assessment"
            ]
            .eq(
                "Potential Finding"
            )
            .sum()
        )

        investigation = int(
            findings_df[
                "Auditor Assessment"
            ]
            .eq(
                "Requires Investigation"
            )
            .sum()
        )

        if (
            "Anomaly Flag"
            in findings_df.columns
        ):

            auditor_identified = int(
                (
                    findings_df[
                        "Anomaly Flag"
                    ]
                    == False
                ).sum()
            )

    if (
        review_df is not None
        and
        not review_df.empty
    ):

        false_positive = int(
            review_df[
                "Auditor Assessment"
            ]
            .eq(
                "False Positive"
            )
            .sum()
        )

    return {

        "total_findings":
            len(findings_df),

        "confirmed_anomalies":
            confirmed,

        "potential_findings":
            potential,

        "requires_investigation":
            investigation,

        "false_positives":
            false_positive,

        "auditor_identified":
            auditor_identified,
    }

# ============================================================
# FINDINGS SUMMARY
# ============================================================

def build_findings_summary():

    findings_df = (
        build_findings_register()
    )

    if findings_df.empty:

        return {

            "open": 0,
            "under_review": 0,
            "validated": 0,
            "dismissed": 0,
            "resolved": 0,

        }

    return {

        "open":
            int(
                findings_df[
                    "Finding Status"
                ]
                .eq("Open")
                .sum()
            ),

        "under_review":
            int(
                findings_df[
                    "Finding Status"
                ]
                .eq("Under Review")
                .sum()
            ),

        "validated":
            int(
                findings_df[
                    "Finding Status"
                ]
                .eq("Validated")
                .sum()
            ),

        "dismissed":
            int(
                findings_df[
                    "Finding Status"
                ]
                .eq("Dismissed")
                .sum()
            ),

        "resolved":
            int(
                findings_df[
                    "Finding Status"
                ]
                .eq("Resolved")
                .sum()
            ),
    }

# ============================================================
# DATASET LINEAGE
# ============================================================

def build_dataset_lineage():

    session = get_session()

    versions = (
        session.analysis.get(
            "dataset_versions",
            {},
        )
    )

    metadata = (
        session.analysis.get(
            "dataset_version_metadata",
            {},
        )
    )

    lineage = []

    for version, df in versions.items():

        info = metadata.get(
            version,
            {},
        )

        lineage.append(
            {
                "version":
                    version,

                "stage":
                    info.get(
                        "stage",
                        "Unknown",
                    ),

                "action":
                    info.get(
                        "action",
                        "Unknown",
                    ),

                "records":
                    len(df),

            }
        )

    lineage.sort(
        key=lambda x:
            x["version"]
    )

    return lineage

# ============================================================
# AUDIT TRAIL
# ============================================================

def build_audit_trail():

    session = get_session()

    return list(
        session.audit_log
    )

# ============================================================
# REPORT PAYLOAD
# ============================================================

def build_report_payload():

    if (
        not report_generation_allowed()
    ):

        raise PermissionError(
            "Report generation "
            "is currently locked."
        )

    payload = {

        "generated_at":
            build_timestamp(),

        "dataset_summary":
            build_dataset_summary(),

        "data_preparation":
            build_data_preparation_summary(),

        "duplicate_review":
            build_duplicate_review_summary(),

        "analysis_summary":
            build_analysis_summary(),

        "explainability_summary":
            build_explainability_summary(),

        "executive_summary":
            build_executive_summary(),

        "findings_summary":
            build_findings_summary(),

        "review_dataset":
            build_review_dataset(),

        "findings_register":
            build_findings_register(),

        "dataset_lineage":
            build_dataset_lineage(),

        "audit_trail":
            build_audit_trail(),
    }

    return payload

# ============================================================
# REPORT SUMMARY
# ============================================================

def build_report_summary():

    payload = (
        build_report_payload()
    )

    dataset = (
        payload[
            "dataset_summary"
        ]
    )

    executive = (
        payload[
            "executive_summary"
        ]
    )

    return {

        "dataset":
            dataset[
                "dataset_name"
            ],

        "records":
            dataset[
                "records"
            ],


        "findings":
            executive[
                "total_findings"
            ],

        "confirmed":
            executive[
                "confirmed_anomalies"
            ],

        "generated":
            payload[
                "generated_at"
            ],
    }

# ============================================================
# REPORT STATUS
# ============================================================

def render_report_status():

    if (
        report_generation_allowed()
    ):

        st.success(
            """
Final Audit Report is
available for export.
"""
        )

    else:

        st.warning(
            """
Report generation is locked.

Complete Audit Review
and Findings generation
before creating the report.
"""
        )