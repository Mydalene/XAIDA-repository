import streamlit as st
import pandas as pd

from assistant.assistant_messages import (
    get_assistant_message,
)

from dataset.dataset_manager import (
    register_dataset,
)

from assistant.assistant_actions import (
    execute_action,
)


def render_chat_workspace():

    stage = (
        st.session_state.workflow_stage
    )

    message = (
        get_assistant_message(stage)
    )

    st.markdown(
        f"""
### XAIDA

{message}
"""
    )

    # ==================================================
    # SESSION CREATED
    # ==================================================

    if stage == "session_created":

        uploaded_file = st.file_uploader(
            "Upload Dataset",
            type=[
                "csv",
                "xlsx",
                "xls",
            ],
        )

        st.markdown("**OR**")

        if st.button(
            "Use Sample Dataset",
            use_container_width=True,
        ):
            execute_action(
                "sample_dataset"
            )

        if uploaded_file:

            if uploaded_file.name.endswith(
                ".csv"
            ):
                df = pd.read_csv(
                    uploaded_file
                )

            else:
                df = pd.read_excel(
                    uploaded_file
                )

            register_dataset(
                dataframe=df,
                dataset_name=uploaded_file.name,
            )

            st.rerun()

    # ==================================================
    # DATASET SELECTION
    # ==================================================

    if stage == "sample_dataset_selection":
        
        if st.button(
            "General-Ledger",
            use_container_width=True,
        ):
            execute_action(
                "General-Ledger"
            )

        if st.button(
            "Accounts-Payable",
            use_container_width=True,
        ):
            execute_action(
                "Accounts-Payable"
            )

        if st.button(
            "Accounts-Receivable",
            use_container_width=True,
        ):
            execute_action(
                "Accounts-Receivable"
            )

        if st.button(
            "Expense-Claims",
            use_container_width=True,
        ):
            execute_action(
                "Expense-Claims"
            )

        if st.button(
            "Budget-Forecast",
            use_container_width=True,
        ):
            execute_action(
                "Budget-Forecast"
            )
                
    # ==================================================
    # DATA PREPARED
    # ==================================================

    if stage == "data_prepared":

        st.success(
            "Data preparation completed."
        )

        st.warning(
            f"{st.session_state.duplicate_count} duplicate records detected."
        )

        if st.button(
            "Review Duplicates",
            key="review_duplicates_btn",
            use_container_width=True
        ):
            execute_action(
                "review_duplicates"
            )

    # ==================================================
    # CHAT INPUT
    # ==================================================

    if stage not in [
        "session_created",
        "sample_dataset_selection",
    ]:

        st.chat_input(
            "Ask XAIDA about the current audit session..."
        )

