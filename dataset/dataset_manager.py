# ============================================================
# XAIDA 3.0
# dataset/dataset_manager.py
# ============================================================

import streamlit as st


def register_dataset(
    dataframe,
    dataset_name,
):

    st.session_state.dataset = dataframe

    st.session_state.dataset_name = dataset_name

    st.session_state.workflow_stage = (
        "dataset_loaded"
    )