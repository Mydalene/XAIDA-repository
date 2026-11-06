# ============================================================
# XAIDA 4.0
# ui/evidence/analysis_tab.py
# ============================================================

import pandas as pd
import streamlit as st

from ui.evidence.table_download import (
    dataframe_for_streamlit,
    render_table_download,
)
import plotly.express as px

from assistant.context.methodology_context import (
    build_methodology_context,
)

def render_analysis_tab(
    session,
):
    st.subheader("Anomaly detection", icon=":material/query_stats:")

    stage = session.metadata.get(
        "workflow_stage"
    )

    PRE_ANALYSIS_STAGES = {
        "dataset",
        "data_preparation",
        "duplicate_review",
    }

    if stage in PRE_ANALYSIS_STAGES:
        st.info(
            "Anomaly detection becomes available after data preparation and "
            "duplicate review are complete.",
            icon=":material/hourglass_top:",
        )
        return

    results = (
        session.analysis.get(
            "results"
        )
    )

    analysis_input_df = (
        session.analysis.get(
            "analysis_dataset"
        )
    )

    # =====================================================
    # ANALYSIS INPUT DATASET
    # =====================================================
    if not results:
        st.info(
            "No analysis results are available yet. Run anomaly detection "
            "from the sidebar to continue.",
            icon=":material/play_circle:",
        )
        return

    if analysis_input_df is not None:

        with st.expander(
            "Analysis input dataset",
            expanded=False,
        ):
            st.info(
                "This is the dataset supplied to the anomaly detection engine "
                "after data preparation and duplicate review.",
                icon=":material/info:",
            )

            render_table_download(
                analysis_input_df,
                "Analysis Input Dataset",
                "analysis_input_dataset",
            )
            st.dataframe(
                dataframe_for_streamlit(analysis_input_df),
                width="stretch",
            )

            with st.container(horizontal=True):
                with st.container(border=True):
                    st.metric("Records", len(analysis_input_df))
                with st.container(border=True):
                    st.metric("Columns", len(analysis_input_df.columns))

    # =====================================================
    # ANALYSIS OUTPUT
    # =====================================================

    if (
        results is None
        or
        results.get(
            "analysis_dataframe"
        ) is None
    ):
        st.info(
            "The analysis run did not produce a results table.",
            icon=":material/info:",
        )
        return

    analysis_output_df = (
        results.get(
            "analysis_dataframe"
        )
    )
    anomaly_dataset_version = session.analysis.get(
        "analysis_version"
    )
    st.badge(
        (
            f"Analysis dataset · V{anomaly_dataset_version}"
            if anomaly_dataset_version
            else "Analysis dataset version not recorded"
        ),
        icon=":material/label:",
        color="blue",
    )

    if (
        "Anomaly Flag"
        in analysis_output_df.columns
        and
        "Risk Score"
        in analysis_output_df.columns
    ):
        analysis_output_df = (
            analysis_output_df.sort_values(
                by=[
                    "Anomaly Flag",
                    "Risk Score",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
        )

    with st.expander(
        "Analysis results",
        expanded=True,
    ):
        st.caption("Risk score distribution and record-level classifications")

        # Histogram
        risk_df = (
            analysis_output_df.copy()
        )

        risk_df["Status"] = risk_df["Anomaly Flag"].map(
            lambda flagged: (
                "Anomaly" if bool(flagged) else "Normal"
            )
        )

        threshold = (
            results.get(
                "threshold"
            )
        )

        fig = px.histogram(
            risk_df,
            x="Risk Score",
            color="Status",
            nbins=30,
            opacity=0.75,
            barmode="overlay",
            color_discrete_map={
                "Normal": "#4CAF50",
                "Anomaly": "#F44336",
            },
        )

        if threshold is not None:

            fig.add_vline(
                x=threshold,
                line_width=3,
                line_dash="dash",
                line_color="orange",
                annotation_text=(
                    f"Threshold = {threshold:.4f}"
                ),
                annotation_position="top right",
            )

        fig.update_layout(
            title="Distribution of Risk Scores",
            xaxis_title="Risk Score",
            yaxis_title="Transaction Count",
            legend_title="Classification",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        render_table_download(
            analysis_output_df,
            "Analysis Results",
            "analysis_results",
        )
        st.dataframe(
            dataframe_for_streamlit(analysis_output_df),
            width="stretch",
        )

        methodology = build_methodology_context(
            session,
            results.get("risk_summary", {}),
        )

        flagged_count = int(
        analysis_output_df[
                "Anomaly Flag"
            ].sum()
        )

        with st.container(horizontal=True):
            with st.container(border=True):
                st.metric("Records", len(analysis_output_df))
            with st.container(border=True):
                st.metric("Flagged records", flagged_count)
            with st.container(border=True):
                st.metric("Columns", len(analysis_output_df.columns))

    # =====================================================
    # DETECTION DETAILS
    # =====================================================

        metadata = (
            session.analysis.get(
                "analysis_metadata",
                {},
            )
        )

        scores = (
            results.get(
                "scores"
            )
        )

        if scores is None or len(scores) == 0:
            st.info(
                "No risk scores are available for this analysis run.",
                icon=":material/info:",
            )
            return

        flags = results.get("flags")
        flagged_count = (
            int(flags.sum())
            if flags is not None
            else int(analysis_output_df["Anomaly Flag"].astype(bool).sum())
        )

        total_count = len(
            scores
        )

        flag_rate = (
            flagged_count / total_count * 100
        )

    with st.expander(
        "Detection details",
        expanded=False,
    ):
        with st.container(horizontal=True):
            with st.container(border=True):
                st.metric(
                    "Threshold",
                    f"{threshold:.4f}" if threshold is not None else "—",
                )
            with st.container(border=True):
                st.metric("Flagged records", flagged_count)
            with st.container(border=True):
                st.metric("Flag rate", f"{flag_rate:.2f}%")

        config_df = pd.DataFrame(
            {
                "Parameter": [
                    "Model",
                    "Model Version",
                    "Dataset Version",
                    "Feature Count",
                    "Isolation Forest Weight",
                    "KMeans Weight",
                    "Autoencoder Weight",
                ],
                "Value": [
                    str(metadata.get("model") or "Not recorded"),
                    str(metadata.get("model_version") or "Not recorded"),
                    str(metadata.get("dataset_version") or "Not recorded"),
                    str(
                        metadata.get("feature_count")
                        if metadata.get("feature_count") is not None
                        else "Not recorded"
                    ),
                    "40%",
                    "20%",
                    "40%",
                ],
            }
        )

        render_table_download(
            config_df,
            "Analysis Configuration",
            "analysis_configuration",
        )
        st.dataframe(
            dataframe_for_streamlit(config_df),
            width="stretch",
            hide_index=True,
        )
        with st.container(horizontal=True):
            with st.container(border=True):
                st.metric("Maximum score", f"{scores.max():.4f}")
            with st.container(border=True):
                st.metric("Average score", f"{scores.mean():.4f}")
            with st.container(border=True):
                st.metric("Minimum score", f"{scores.min():.4f}")

# =====================================================
# BAR
# =====================================================

    with st.expander(
        "Highest-risk records",
        expanded=True,
    ):
        top_risk = (
            analysis_output_df
            .sort_values(
                "Risk Score",
                ascending=False,
            )
            .head(10)
            )

        fig = px.bar(
            top_risk,
            x=top_risk.index.astype(str),
            y="Risk Score",
            color="Risk Score",
            title="Top 10 Highest Risk Scores",
        )

        fig.update_layout(
             xaxis_title="Transaction",
            yaxis_title="Risk Score",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )
              
# =====================================================
# TOP RISK TRANSACTIONS
# =====================================================
        analysis_df = (
            results.get(
                "analysis_dataframe"
            )
        )

        if (
            analysis_df is not None
            and
            "Risk Score"
            in analysis_df.columns
        ):
            top_risk = (
                analysis_df
                .sort_values(
                    by="Risk Score",
                    ascending=False,
                )
                .head(10)
            )

            render_table_download(
                top_risk,
                "Top Risk Records",
                "top_risk_records",
            )
            st.dataframe(
                dataframe_for_streamlit(top_risk),
                width="stretch",
                hide_index=True,
            )
