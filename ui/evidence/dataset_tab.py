# ============================================================
# XAIDA 4.0
# ui/evidence/dataset_tab.py
# ============================================================

import streamlit as st



from dataset.version_manager import (
    get_current_version,
    get_dataset_versions,
)
from ui.evidence.table_download import (
    dataframe_for_streamlit,
    render_table_download,
)

def render_dataset_tab(
    session,
):

    if (
        session.dataset.get(
            "dataframe"
        )
        is None
    ):
        with st.container(border=True):
            st.subheader(
                "Start with a dataset",
                icon=":material/database:",
            )
            st.write(
                "Upload an audit dataset to begin reviewing records, "
                "analysis results, and supporting evidence."
            )
            st.caption(
                "Use the dataset upload or sample dataset controls in the "
                "sidebar to get started."
            )
        return

    st.subheader("Dataset", icon=":material/database:")
    current_version = get_current_version(session)
    st.badge(
        f"Current dataset · V{current_version}",
        icon=":material/label:",
        color="blue",
    )

    profile = session.dataset.get("profile", {})
    with st.container(horizontal=True):
        if session.dataset.get("dataset_name"):
            with st.container(border=True):
                st.metric("Source file", session.dataset["dataset_name"])
        if "memory_usage_mb" in profile:
            with st.container(border=True):
                st.metric(
                    "Memory",
                    f"{profile['memory_usage_mb']:.2f} MB",
                )
        if "numeric_columns" in profile:
            with st.container(border=True):
                st.metric("Numeric fields", profile["numeric_columns"])
        if "categorical_columns" in profile:
            with st.container(border=True):
                st.metric(
                    "Categorical fields",
                    profile["categorical_columns"],
                )

    dataframe = get_dataset_versions(session).get(
        current_version,
        session.dataset.get("dataframe"),
    )
    display_df = dataframe

    if (
        display_df is not None
        and "Anomaly Flag" in display_df.columns
        and "Risk Score" in display_df.columns
    ):
        display_df = display_df.sort_values(
            by=["Anomaly Flag", "Risk Score"],
            ascending=[False, False],
        )

    with st.container(border=True):
        st.markdown("**Dataset preview**")
        st.caption(
            "Review the loaded records below. Changes in this preview are "
            "saved to the current session dataset."
        )
        edited_df = st.data_editor(
            dataframe_for_streamlit(display_df),
            width="stretch",
            hide_index=True,
            key="dataset_preview_editor",
        )
        render_table_download(
            edited_df,
            "Dataset Preview",
            f"dataset_preview_v{current_version}",
        )
        st.caption(f"{len(edited_df):,} records")
