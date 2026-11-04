import streamlit as st

from assistant.assistant_actions import (
    execute_action,
)

def render_results_dashboard():

    stage = st.session_state.get(
        "workflow_stage"
    )

    if stage in [
        "session_created",
        "sample_dataset_selection",
    ]:
        st.info(
            "Awaiting dataset selection."
        )
        return

    if stage == "duplicate_review":

        duplicates = (
            st.session_state.duplicate_results
        )

        if duplicates is not None:

            if (
                st.session_state.duplicate_review_results
                is None
            ):
                review_df = duplicates.copy()

                review_df["Retain"] = True
                review_df["Resolution"] = "Pending"
                review_df["Reviewer Notes"] = ""

                st.session_state.duplicate_review_results = (
                    review_df
                )

            review_df = (
                st.session_state.duplicate_review_results
            )

            if "Retain" not in review_df.columns:
                review_df["Retain"] = True
                review_df["Resolution"] = "Pending"
                review_df["Reviewer Notes"] = ""

            st.subheader(
                "Duplicate Resolution"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Records Removed",
                    st.session_state.get(
                        "duplicates_removed",
                        0,
                    ),
                )

            with col2:
                st.metric(
                    "Strategy",
                    st.session_state.get(
                        "duplicate_strategy",
                        "-",
                    ),
                )
                
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(
                    "Drop All Duplication (Keep first record)",
                    use_container_width=True
                ):
                    execute_action(
                        "drop_all_duplicates"
                    )

            with col2:
                if st.button(
                    "Retain All Duplicates",
                    use_container_width=True
                ):
                    execute_action(
                        "retain_all_duplicates"
                    )

            with col3:
                st.info(
                    "Or review records individually below."
                )

            st.info(
                """
                Review duplicate records. 
                Keep the records that should
                remain in the analysis dataset. 
                Uncheck records to exclude.
                """
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Duplicate Groups",
                    duplicates[
                        "Duplicate Group"
                    ].nunique()
                )

            with col2:
                st.metric(
                    "Duplicate Records",
                    len(duplicates)
                )

            edited_df = st.data_editor(
                review_df,
                use_container_width=True,
                height=400,
            )

            retained_count = int(
                edited_df["Retain"].sum()
            )

            with col3:
                st.metric(
                    "Records Retained",
                    retained_count
                )
                
            if st.button(
                "Confirm Duplicate Review",
                use_container_width=True,
            ):

                execute_action(
                    (
                        "confirm_duplicate_review",
                        edited_df,
                    )
                )

            
    if stage in [
        "analysis_ready",
        "analysis_ready_no_duplicates",
    ]:

        st.subheader(
            "Final Analysis Dataset"
        )

        analysis = (
            st.session_state.analysis
        )

        if analysis is None:

            analysis = (
                st.session_state.dataset
            )

        original_count = len(
            st.session_state.dataset
        )

        analysis_count = len(
            analysis
        )

        removed_count = max(
            0,
            original_count
            - analysis_count
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Original Records",
                original_count
            )

        with col2:
            st.metric(
                "Records Removed",
                removed_count
            )

        with col3:
            st.metric(
                "Records for Analysis",
                analysis_count
            )

        st.dataframe(
            analysis.head(20),
            use_container_width=True,
            height=350,
        )

        if st.button(
            "Run Analysis",
            key="run_analysis_btn",
            use_container_width=True,
        ):
            execute_action(
                "run_analysis"
            )

    if stage == "analysis_complete":

        results = (
            st.session_state.analysis_results
        )

        st.subheader(
            "Analysis Results"
        )

        summary = (
            st.session_state.risk_summary
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Flagged Transactions",
                summary.get(
                    "flagged_transactions",
                    0,
                )
            )

        with col2:

            st.metric(
                "High Risk",
                summary.get(
                    "high_risk_transactions",
                    0,
                )
            )

        with col3:

            st.metric(
                "Risk Level",
                summary.get(
                    "risk_level",
                    "Unknown",
                )
            )

        st.subheader(
            "Flagged Records"
        )

        st.dataframe(
            st.session_state.flagged_transactions,
            use_container_width=True,
        )