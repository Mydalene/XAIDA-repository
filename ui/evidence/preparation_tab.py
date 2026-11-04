# ============================================================
# XAIDA 4.0
# ui/evidence/preparation_tab.py
# ============================================================

import pandas as pd
import streamlit as st

from assistant.context.methodology_context import (
    build_methodology_context,
)
from ui.evidence.table_download import (
    render_table_download,
)

def render_preparation_tab(
    session,
):
    if (
        session.dataset.get("dataframe") is None
        or not session.dataset.get("data_preparation_complete", False)
    ):
        st.info(
            "Preparation results are not available yet. Upload a dataset and "
            "run data preparation from the sidebar to continue.",
            icon=":material/tune:",
        )
        return

    st.subheader("Data preparation", icon=":material/tune:")
    results = session.analysis.get("results") or {}
    methodology = build_methodology_context(
        session,
        results.get("risk_summary", {}),
    )

    missing_summary = (
        session.dataset.get(
            "missing_summary"
        )
    )

    # =====================================================
    # DATA PREPARATION SUMMARY
    # =====================================================

    missing_count = 0
    if missing_summary is not None and not missing_summary.empty:
        if "Missing Count" in missing_summary.columns:
            missing_count = int(missing_summary["Missing Count"].sum())
        elif "missing_count" in missing_summary.columns:
            missing_count = int(missing_summary["missing_count"].sum())

    with st.container(horizontal=True):
        with st.container(border=True):
            st.metric(
                "Records prepared",
                session.dataset.get(
                    "rows",
                    0,
                ),
            )
        with st.container(border=True):
            st.metric(
                "Missing values",
                missing_count,
            )

    # =====================================================
    # MISSING VALUES SUMMARY
    # =====================================================

    if (
        missing_summary
        is not None
    ):
        with st.expander(
            "Missing values by field",
            expanded=False,
        ):
            render_table_download(
                missing_summary,
                "Missing Values Summary",
                "missing_values_summary",
            )
            st.dataframe(
                missing_summary,
                width="stretch",
                hide_index=True,
            )

    # =====================================================
    # NULL CLASSIFICATION
    # =====================================================

    classification = (
        session.dataset.get(
            "missing_classification"
        )
    )

    if classification:

        st.subheader(
            "Null Classification"
        )

        valid = (
            classification[
                "business_valid"
            ]
        )

        unexpected = (
            classification[
                "unexpected"
            ]
        )

        if valid:
            st.success(
                "Business-valid null values detected."
            )

        if unexpected:
            st.warning(
                "Unexpected null values detected."
            )

    # =====================================================
    # IMPUTATION LOG
    # =====================================================

    imputation_log = (
        session.dataset.get(
            "imputation_log"
        )
    )

    if imputation_log:

        with st.expander(
            "Imputation Rules Applied",
            expanded=False,
        ):
            imputation_df = pd.DataFrame(imputation_log)
            render_table_download(
                imputation_df,
                "Imputation Rules",
                "imputation_rules",
            )
            st.dataframe(
                imputation_df,
                width="stretch",
                hide_index=True,
            )