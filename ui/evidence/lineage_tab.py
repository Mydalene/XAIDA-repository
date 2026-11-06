# ============================================================
# XAIDA 4.0
# ui/evidence/lineage_tab.py
# ============================================================

import pandas as pd
import streamlit as st

from dataset.version_manager import (
    get_dataset_versions,
    get_version_metadata,
)

from audit.change_tracker import (
    get_change_log,
)

from ui.evidence.table_download import (
    dataframe_for_streamlit,
    render_table_download,
)


def render_lineage_tab(
    session,
):

    versions = (
        get_dataset_versions(
            session
        )
    )

    if not versions:
        st.info(
            "Dataset versions will appear here after a dataset is loaded.",
            icon=":material/history:",
        )
        return

    st.subheader("Dataset lineage", icon=":material/account_tree:")
    
    metadata = (
        get_version_metadata(
            session
        )
    )

    lineage_df = pd.DataFrame(
        [
            {
                "Version": f"V{v}",
                "Stage": metadata.get(
                    v,
                    {},
                ).get(
                    "stage",
                    "Unknown",
                ),
                "Action": metadata.get(
                    v,
                    {},
                ).get(
                    "action",
                    "Unknown",
                ),
                "Dataset Type": metadata.get(
                    v,
                    {},
                ).get(
                    "dataset_type",
                    "Source / transformed",
                ),
                "Records": len(df),
                "Columns": len(
                    df.columns
                ),
            }
            for v, df in versions.items()
        ]
    )

    with st.container(border=True):
        st.markdown("**Version history**")
        st.caption("A record of the dataset versions created during this audit.")
        render_table_download(
            lineage_df,
            "Dataset Version History",
            "dataset_version_history",
        )
        st.dataframe(
            dataframe_for_streamlit(lineage_df),
            width="stretch",
            hide_index=True,
        )

    selected_version = st.selectbox(
        "Inspect a dataset version",
        sorted(
            versions.keys()
        ),
        format_func=lambda x:
            f"Version {x}",
    )

    selected_df = (
        versions[
            selected_version
        ]
    )

    with st.container(border=True):
        st.markdown(f"**Dataset version V{selected_version}**")
        render_table_download(
            selected_df,
            f"Dataset Version V{selected_version}",
            f"dataset_version_v{selected_version}",
        )
        st.dataframe(
            dataframe_for_streamlit(selected_df),
            width="stretch",
            hide_index=True,
        )

    st.subheader("Change history", icon=":material/manage_history:")

    changes = (
        get_change_log(
            session
        )
    )

    if changes:
        changes_df = pd.DataFrame(changes)
        with st.container(border=True):
            render_table_download(
                changes_df,
                "Dataset Change History",
                "dataset_change_history",
            )
            st.dataframe(
                dataframe_for_streamlit(changes_df),
                width="stretch",
                hide_index=True,
            )
    else:
        st.info(
            "No dataset changes have been recorded.",
            icon=":material/info:",
        )

    # ============================================================
    # REMOVED DUPLICATE RECORDS
    # ============================================================

    removed_duplicates = (
        session.duplicates.get(
            "removed_duplicate_records"
        )
    )

    if (
        removed_duplicates is not None
        and
        not removed_duplicates.empty
    ):

        st.subheader(
            "Removed duplicate records",
            icon=":material/delete_sweep:",
        )

        with st.container(horizontal=True):
            with st.container(border=True):
                st.metric("Records removed", len(removed_duplicates))
            with st.container(border=True):
                st.metric(
                    "Removal strategy",
                    session.duplicates.get(
                        "strategy",
                        "Manual Review",
                    ),
                )

        with st.container(border=True):
            render_table_download(
                removed_duplicates,
                "Removed Duplicate Records",
                "removed_duplicate_records",
            )
            st.dataframe(
                dataframe_for_streamlit(removed_duplicates),
                width="stretch",
                height=300,
                hide_index=True,
            )