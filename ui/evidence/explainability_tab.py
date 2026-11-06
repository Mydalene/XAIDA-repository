# ============================================================
# XAIDA 4.0
# ui/evidence/explainability_tab.py
# ============================================================

import pandas as pd
import streamlit as st
import plotly.express as px

from ui.evidence.table_download import (
    dataframe_for_streamlit,
    render_table_download,
)


def render_explainability_tab(
    session,
):
    st.subheader("Explainability", icon=":material/psychology:")

    analysis_complete = (
        session.analysis.get(
            "analysis_complete",
            False,
        )
    )

    if not analysis_complete:
        st.info(
            "Explanations become available after anomaly detection is "
            "complete.",
            icon=":material/hourglass_top:",
        )
        return

    explainability_version = session.analysis.get(
        "explainability_version"
    )
    st.badge(
        (
            f"Explainability dataset · V{explainability_version}"
            if explainability_version
            else "Explainability dataset version not generated"
        ),
        icon=":material/label:",
        color="blue",
    )

    explanations = (
        session.explainability.get(
            "explanations",
            []
        )
    )

    results = (
        session.analysis.get(
            "results"
        )
    )

    # =====================================================
    # SHAP EXPLAINABILITY
    # =====================================================

    if not results:
        st.info(
            "Analysis results are not available. Run anomaly detection "
            "before reviewing explanations.",
            icon=":material/query_stats:",
        )
        return

    explanations = (
        results.get(
            "explanations",
            []
        )
    )

    session.explainability[
        "narratives"
    ] = explanations

    top_features = (
        results.get(
            "top_features"
        )
    )

    session.explainability[
        "top_features"
    ] = top_features

    analysis_output_df = (
        results.get(
            "analysis_dataframe"
        )
    )
    explained_record_count = sum(
        explanation is not None and str(explanation).strip() != ""
        for explanation in explanations
    )
    flagged_record_count = (
        int(
            analysis_output_df["Anomaly Flag"]
            .fillna(False)
            .astype(bool)
            .sum()
        )
        if analysis_output_df is not None
        and "Anomaly Flag" in analysis_output_df.columns
        else 0
    )
    explainability_coverage = (
        min(explained_record_count / flagged_record_count * 100, 100)
        if flagged_record_count
        else 100
    )

    with st.expander(
        "Transaction explanations",
        expanded=False,
    ):
        # Transaction explanations
        st.markdown("**Flagged records and key drivers**")

        formatted_explanations = []

        for explanation in explanations:

            formatted_explanations.append(
                str(explanation)
                .replace(
                    "num__",
                    ""
                )
                .replace(
                    "cat__",
                    ""
                )
                .replace(
                    "_",
                    " "
                )
                .title()
            )

        if (
            analysis_output_df is not None
            and
            len(formatted_explanations) > 0
        ):

            flagged_df = (
                analysis_output_df[
                    analysis_output_df[
                        "Anomaly Flag"
                    ] == 1
                ]
                .copy()
            )

            flagged_df.insert(
                0,
                "Source Record",
                flagged_df.index
            )

            flagged_df = (
                flagged_df.head(
                    len(
                        formatted_explanations
                    )
                )
            )

            flagged_df[
                "Key Drivers"
            ] = formatted_explanations

            session.explainability[
                "explained_records"
            ] = (
                flagged_df[
                    [
                        "Source Record",
                        "Risk Score",
                        "Key Drivers",
                    ]
                ]
                .head(50)
                .copy()
                .to_dict("records")
            )

            display_cols = []

            if (
                "Transaction ID"
                in flagged_df.columns
            ):
                display_cols.append(
                    "Transaction ID"
                )

            display_cols.extend(
                [
                    "Source Record",
                    "Risk Score",
                    "Key Drivers",
                ]
            )


            flagged_display_df = flagged_df[display_cols]
            render_table_download(
                flagged_display_df,
                "Flagged Records and Key Drivers",
                "flagged_records_key_drivers",
            )
            selection = st.dataframe(
                dataframe_for_streamlit(flagged_display_df),
                width="stretch",
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            selected_row = None
                
            if (
                selection
                and
                selection.selection.rows
            ):

                selected_idx = (
                    selection.selection.rows[0]
                )

                selected_row = (
                    flagged_df.iloc[
                        selected_idx
                    ]
                )

                session.explainability[
                    "selected_row"
                ] = selected_row.to_dict()

                session.explainability[
                    "selected_record"
                ] = int(
                    selected_row[
                        "Source Record"
                    ]
                )

                session.explainability[
                    "selected_key_drivers"
                ] = str(
                    selected_row[
                        "Key Drivers"
                    ]
                )

                session.explainability[
                    "selected_risk_score"
                ] = float(
                    selected_row[
                        "Risk Score"
                    ]
                )

            # Explainability narrative
            st.subheader(
                "Selected record explanation",
                icon=":material/lightbulb:",
            )

            if selected_row is None:
                selected_row = session.explainability.get("selected_row")
            if selected_row is not None:
                with st.container(border=True):
                    record_col, score_col = st.columns(2)
                    with record_col:
                        st.metric(
                            "Source record",
                            selected_row["Source Record"],
                        )
                    with score_col:
                        st.metric(
                            "Risk score",
                            f"{selected_row['Risk Score']:.4f}",
                        )
                    st.markdown("**Key drivers**")
                    st.write(selected_row["Key Drivers"])
                    st.caption(
                        "These characteristics contributed most to the "
                        "record's anomaly score. They indicate unusual "
                        "patterns and are not, by themselves, evidence of "
                        "fraud or control failure."
                    )
            else:
                st.info(
                    "Select a record above to review its detailed "
                    "explanation.",
                    icon=":material/touch_app:",
                )

        else:

            st.info(
                "No transaction explanations are available.",
                icon=":material/info:",
            )

        st.subheader(
            "Interpretation guidance",
            icon=":material/menu_book:",
        )

        st.info(
            """
        Feature importance scores indicate
        which transaction characteristics had
        the greatest influence on anomaly
        detection.

        A high importance score does not
        necessarily indicate an error,
        fraudulent activity, or control
        failure. Rather, it indicates that
        the transaction differs from normal
        behaviour for that specific
        characteristic.

        Auditors should evaluate whether the
        identified differences can be
        explained by legitimate business
        activity.
            """
        )

    with st.expander(
        "Feature drivers",
        expanded=True,
    ):
        st.subheader(
            "Top feature drivers",
            icon=":material/leaderboard:",
        )

        display_features = None

        if (
            top_features is not None
            and
            not top_features.empty
        ):

            display_features = (
                top_features.copy()
            )

            display_features["feature"] = (
                display_features["feature"]
                .astype(str)
                .str.replace(
                    "num__",
                    "",
                    regex=False,
                )
                .str.replace(
                    "cat__",
                    "",
                    regex=False,
                )
                .str.replace(
                    "_",
                    " ",
                    regex=False,
                )
                .str.title()
                )

            display_features = (
                display_features.rename(
                    columns={
                        "feature":
                            "Feature Driver",
                        "importance":
                            "Importance Score",
                    }
                )
            )

            fig = px.bar(
                display_features.head(10),
                x="Importance Score",
                y="Feature Driver",
                orientation="h",
                color="Importance Score",
            )

            fig.update_layout(
                title="Top SHAP Feature Drivers",
                yaxis={
                    "categoryorder":
                    "total ascending"
                }
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )
                    
        else:

            st.info(
                "No feature importance data is available.",
                icon=":material/info:",
            )

    with st.expander(
        "Explainability details",
        expanded=False,
    ):

        st.subheader(
            "How to read these explanations",
            icon=":material/info:",
        )

        st.write(
            """
            SHAP (SHapley Additive exPlanations)
            was used to determine how individual
            features contributed to anomaly scores.

            Higher importance scores indicate that
            a feature had a greater influence on
            the identification of anomalous
            transactions.
            """
        )

        if (
            display_features is not None
            and
            not display_features.empty
        ):

            attribution_df = (
                display_features.copy()
            )

            attribution_df[
                "Contribution Level"
            ] = pd.qcut(
                attribution_df[
                    "Importance Score"
                ],
                q=3,
                labels=[
                    "Low",
                    "Moderate",
                    "High",
                ],
                duplicates="drop",
            )

            render_table_download(
                attribution_df,
                "Feature Attribution",
                "feature_attribution",
            )
            st.dataframe(
                dataframe_for_streamlit(attribution_df),
                width="stretch",
                hide_index=True,
            )

        st.subheader(
            "Explainability Statistics"
        )

        with st.container(horizontal=True):
            with st.container(border=True):
                st.metric("Explained transactions", explained_record_count)
            with st.container(border=True):
                st.metric(
                    "Top drivers",
                    len(display_features) if display_features is not None else 0,
                )
            with st.container(border=True):
                st.metric(
                    "Explainability coverage",
                    f"{explainability_coverage:.0f}%",
                )
