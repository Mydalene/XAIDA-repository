# ============================================================
# XAIDA 4.0
# ui/evidence/duplicate_tab.py
# ============================================================

import streamlit as st

from ui.action_dialog import ACTION_DIALOG_KEY
from ui.evidence.table_download import (
    render_table_download,
)


def render_duplicate_tab(
    session,
):

    stage = session.metadata.get(
        "workflow_stage"
    )

    duplicate_count = session.duplicates.get(
        "duplicate_count",
        0,
    )

    st.subheader("Duplicate review", icon=":material/content_copy:")

    # Dataset stage
    if stage == "dataset":
        st.info(
            "Run data preparation to detect potential duplicate records.",
            icon=":material/tune:",
        )
        return

    # Preparation stage
    if stage == "data_preparation":

        if duplicate_count > 0:
            st.info(
                f"{duplicate_count:,} potential duplicate records were "
                "identified. Continue to duplicate review to inspect them.",
                icon=":material/content_copy:",
            )
        else:
            st.info(
                "No duplicate records were identified. Duplicate review is "
                "not required; continue directly to anomaly detection.",
                icon=":material/check_circle:",
            )

        return

    duplicates = (
        session.duplicates.get(
            "duplicate_records"
        )
    )

    summary = (
        session.analysis.get(
            "analysis_dataset_summary",
            {},
        )
    )

    strategy = (
        summary.get(
            "strategy"
        )
        if summary
        else None
    )

    if (
        duplicates is None
        or duplicates.empty
    ):
        st.info(
            "No duplicate records are available for review.",
            icon=":material/check_circle:",
        )
        return

    with st.container(horizontal=True):
        with st.container(border=True):
            st.metric(
                "Duplicate records",
                session.duplicates.get("duplicate_count", 0),
            )
        with st.container(border=True):
            st.metric(
                "Duplicate groups",
                session.duplicates.get("duplicate_groups", 0),
            )

    duplicate_review_complete = (
        session.duplicates.get(
            "duplicate_review_complete",
            True,
        )
    )

    selected_rows = (
        session.duplicates.get(
            "selected_duplicate_count",
            0,
        )
    )
        
    with st.container(border=True):
        st.markdown("**Duplicate records**")
        render_table_download(
            duplicates,
            "Duplicate Preview",
            "duplicate_preview",
        )

        pending_dialog = st.session_state.get(ACTION_DIALOG_KEY, {})
        confirmation_pending = (
            pending_dialog.get("mode") == "confirmation"
            and pending_dialog.get("action") == "remove_manual_duplicates"
        )

        if (
            strategy
            == "manual_duplicate_review"
            and
            not duplicate_review_complete
            and
            not confirmation_pending
        ):

            selection = st.dataframe(
                duplicates,
                width="stretch",
                on_select="rerun",
                selection_mode="multi-row",
            )

            selected_positions = (
                selection.selection.rows
            )

            session.duplicates[
                "selected_duplicate_rows"
            ] = selected_positions

            session.duplicates[
                "selected_duplicate_count"
            ] = len(
                selected_positions
            )

            if len(selected_positions) > 0:

                st.info(
                    f"{len(selected_positions)} rows selected."
                )

        else:

            st.dataframe(
                duplicates,
                width="stretch",
            )

            session.duplicates[
                "selected_duplicate_rows"
            ] = []

            session.duplicates[
                "selected_duplicate_count"
            ] = 0
            
    if (
        strategy
        and
        session.duplicates.get(
            "duplicate_review_complete",
            False,
        )
    ):


        with st.container(horizontal=True):
            with st.container(border=True):
                st.metric("Original records", summary.get("original_records", 0))
            with st.container(border=True):
                st.metric("Records removed", summary.get("records_removed", 0))
            with st.container(border=True):
                st.metric("Records retained", summary.get("records_retained", 0))

    else:

        st.info(
            "Review the duplicate population and choose a resolution strategy "
            "from the sidebar to continue.",
            icon=":material/info:",
        )