# ============================================================
# XAIDA 5.0
# ui/evidence/audit_review_tab.py
# ============================================================

import logging
import sqlite3

import streamlit as st
import pandas as pd

from assistant.evaluation_store import record_audit_review_metrics
from dataset.version_manager import (
    get_current_version,
    get_dataset_versions,
)
from ui.evidence.table_download import (
    dataframe_for_streamlit,
    render_table_download,
)

logger = logging.getLogger(__name__)


def calculate_audit_review_metrics(dataframe):
    flags = dataframe.get(
        "Anomaly Flag",
        pd.Series(False, index=dataframe.index),
    ).fillna(False).eq(True)
    assessments = dataframe.get(
        "Auditor Assessment",
        pd.Series(None, index=dataframe.index, dtype=object),
    )
    blank_assessments = (
        assessments.fillna("")
        .astype(str)
        .str.strip()
        .eq("")
    )
    auditor_classifications = assessments.isin(
        [
            "Confirmed Anomaly",
            "Potential Finding",
            "Requires Investigation",
        ]
    )

    return {
        "total_records": int(len(dataframe)),
        "ai_flagged_records": int(flags.sum()),
        "auditor_identified": int((~flags & auditor_classifications).sum()),
        "unassessed_records": int((~flags & assessments.isna()).sum()),
        "remaining_reviews": int((flags & blank_assessments).sum()),
        "confirmed_anomalies": int(
            assessments.eq("Confirmed Anomaly").sum()
        ),
        "requires_investigation": int(
            assessments.eq("Requires Investigation").sum()
        ),
        "potential_findings": int(
            assessments.eq("Potential Finding").sum()
        ),
        "false_positives": int(assessments.eq("False Positive").sum()),
    }


def render_audit_review_tab(
    session,
):
    st.subheader("Audit review", icon=":material/rule:")

    stage = session.metadata.get(
        "workflow_stage"
    )

    REVIEW_AVAILABLE_STAGES = {
        "audit_review",
        "findings",
        "reporting",
        "audit_completion",
    }

    if stage not in REVIEW_AVAILABLE_STAGES:
        st.info(
            "Audit review opens after anomaly detection. Complete the earlier "
            "workflow stages to continue.",
            icon=":material/hourglass_top:",
        )
        return


    current_version = (
        get_current_version(
            session
        )
    )

    dataset_versions = (
        get_dataset_versions(
            session
        )
    )

    dataframe = (
        session.review.get(
            "records"
        )
    )

    review_version = session.review.get("review_version")
    if review_version != current_version:
        dataframe = dataset_versions.get(current_version)
        if dataframe is not None:
            dataframe = dataframe.copy()
            session.review["records"] = dataframe.copy()
            session.review["review_version"] = current_version

    if (
        dataframe is not None
        and
        not isinstance(
            dataframe,
            pd.DataFrame,
        )
    ):
        dataframe = None

    if dataframe is None:

        dataframe = (
            dataset_versions.get(
                current_version
            )
        )

        if dataframe is not None:

            dataframe = (
                dataframe.copy()
            )

            session.review[
                "records"
            ] = dataframe.copy()
            session.review["review_version"] = current_version

    if dataframe is None:
        st.info(
            "No dataset records are available for audit review.",
            icon=":material/info:",
        )
        return


    #
    # Review columns
    #

    if (
        "Auditor Assessment"
        not in dataframe.columns
    ):
        dataframe[
            "Auditor Assessment"
        ] = None
    
    if (
        "Auditor Comment"
        not in dataframe.columns
    ):
        dataframe[
            "Auditor Comment"
        ] = ""

    #
    # Sort anomalies first
    #

    sort_columns = []

    if (
        "Anomaly Flag"
        in dataframe.columns
    ):
        sort_columns.append(
            "Anomaly Flag"
        )

    if (
        "Risk Score"
        in dataframe.columns
    ):
        sort_columns.append(
            "Risk Score"
        )

    if sort_columns:

        dataframe = (
            dataframe.sort_values(
                by=sort_columns,
                ascending=False,
            )
        )

    #
    # Metrics
    #

    metrics = calculate_audit_review_metrics(dataframe)
    total_records = metrics["total_records"]
    flagged_records = metrics["ai_flagged_records"]
    auditor_identified = metrics["auditor_identified"]
    remaining_unassessed = metrics["unassessed_records"]
    remaining_reviews = metrics["remaining_reviews"]
    confirmed_anomalies = metrics["confirmed_anomalies"]
    requires_investigation = metrics["requires_investigation"]
    potential_findings = metrics["potential_findings"]
    false_positives = metrics["false_positives"]

    session.review[
        "remaining_reviews"
    ] = int(
        remaining_reviews
    )

    st.badge(
        f"Dataset version · V{current_version}",
        icon=":material/label:",
        color="blue",
    )
    explainability_version = session.analysis.get(
        "explainability_version"
    )
    if explainability_version is not None:
        st.caption(
            "Explainability-enriched dataset · "
            f"V{explainability_version}"
        )

    with st.container(horizontal=True):
        for label, value in (
            ("Records", total_records),
            ("AI-flagged", flagged_records),
            ("Auditor-identified", int(auditor_identified)),
            ("Unassessed", int(remaining_unassessed)),
            ("Reviews remaining", int(remaining_reviews)),
        ):
            with st.container(border=True):
                st.metric(label, value)

    with st.expander("Assessment summary", expanded=False):
        with st.container(horizontal=True):
            for label, value in (
                ("Confirmed anomalies", int(confirmed_anomalies)),
                ("Requires investigation", int(requires_investigation)),
                ("Potential findings", int(potential_findings)),
                ("False positives", int(false_positives)),
            ):
                with st.container(border=True):
                    st.metric(label, value)

    if session.review.get(
        "manual_review_mode",
        False,
    ):
        st.info(
            "Manual review is active. Use the Auditor Assessment column to "
            "classify flagged records individually.",
            icon=":material/edit_note:",
        )
        
    review_locked = (
        session.review.get(
            "audit_review_complete",
            False,
        )
    )

    with st.container(border=True):
        st.markdown(
            "**Review records**"
            if not review_locked
            else "**Review records · read-only**"
        )
        edited_df = st.data_editor(
            dataframe_for_streamlit(dataframe),
            width="stretch",
            hide_index=True,
            disabled=review_locked,
            key=f"audit_review_editor_v{current_version}",
            column_config={
                "Auditor Assessment": st.column_config.SelectboxColumn(
                    "Auditor Assessment",
                    options=[
                        "Confirmed Anomaly",
                        "Potential Finding",
                        "False Positive",
                        "Requires Investigation",
                    ],
                    required=False,
                ),
                "Auditor Comment": st.column_config.TextColumn(
                    "Auditor Comment",
                    width="large",
                ),
            },
        )

    render_table_download(
        edited_df,
        "Audit Review Records",
        f"audit_review_records_v{current_version}",
    )

    session.review[
        "records"
    ] = edited_df.copy()


    metrics = calculate_audit_review_metrics(edited_df)
    session.review["audit_review_metrics"] = metrics
    session.review[
        "remaining_reviews"
    ] = metrics["remaining_reviews"]

    try:
        record_audit_review_metrics(
            audit_session_id=session.metadata["session_id"],
            dataset_version=current_version,
            metrics=metrics,
        )
    except sqlite3.Error:
        logger.exception("XAIDA audit review metrics could not be saved.")
        st.error(
            "Audit review metrics could not be saved to SQLite. "
            "Notify the application administrator."
        )
