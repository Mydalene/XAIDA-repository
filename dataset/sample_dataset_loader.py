# ============================================================
# XAIDA 4.0
# dataset/sample_dataset_loader.py
# ============================================================
import streamlit as st

from pathlib import Path
import pandas as pd

from orchestration.workflow_engine import (
    transition_to,
    DATASET,
)

from audit.audit_logger import (
    log_audit_event,
)

# ============================================================
# SAMPLE DATASETS
# ============================================================

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)

SAMPLE_DATASETS = {
    "Accounts Payable":
        BASE_DIR
        / "sample_dataset"
        / "Accounts-Payable.csv",

    "Accounts Receivable":
        BASE_DIR
        / "sample_dataset"
        / "Accounts-Receivable.csv",

    "Budget Forecast":
        BASE_DIR
        / "sample_dataset"
        / "Budget-Forecast.csv",

    "Expense Claims":
        BASE_DIR
        / "sample_dataset"
        / "Expense-Claims.csv",

    "General Ledger":
        BASE_DIR
        / "sample_dataset"
        / "General-Ledger.csv",
}

# ============================================================
# LOAD SAMPLE DATASET
# ============================================================

def load_sample_dataset(
    session,
    dataset_name,
):

    file_path = SAMPLE_DATASETS[
        dataset_name
    ]

    if not file_path.exists():

        raise FileNotFoundError(
            f"Sample dataset not found: {file_path}"
        )

    # ===========================================
    # LOAD DATAFRAME
    # ===========================================

    dataframe = pd.read_csv(
        file_path
    )

    # ===========================================
    # UPDATE SESSION DATASET
    # ===========================================

    session.dataset[
        "dataset_name"
    ] = file_path.name

    session.dataset[
        "dataframe"
    ] = dataframe

    session.dataset["parsing_status"] = "Completed"
    session.dataset["validation_status"] = "Pending"
    session.dataset["validation_results"] = {}

    session.dataset[
        "rows"
    ] = len(
        dataframe
    )

    session.dataset[
        "columns"
    ] = len(
        dataframe.columns
    )

    session.dataset[
        "loaded"
    ] = True

    session.initialization[
        "dataset_selected"
    ] = True

    session.initialization[
        "dataset_loaded"
    ] = True

    session.initialization[
        "upload_method"
    ] = "sample_dataset"

    session.initialization[
        "dataset_source"
    ] = dataset_name

    session.initialization[
        "sample_dataset"
    ] = dataset_name

    session.initialization[
        "initialization_complete"
    ] = True

    transition_to(
        session,
        DATASET,
    )
    
    st.session_state[
        "active_tab"
    ] = "Dataset"

    # ===========================================
    # RESET GOVERNANCE
    # ===========================================

    session.analysis[
        "dataset_version"
    ] = 1

    session.analysis[
        "dataset_versions"
    ] = {
        1: dataframe.copy()
    }

    session.analysis[
        "dataset_version_metadata"
    ] = {
        1: {
            "stage":
                "Dataset",
            "action":
                "Dataset Upload",
        }
    }
    
    session.analysis[
        "analysis_version"
    ] = 0

    session.analysis[
        "analysis_required"
    ] = False

    log_audit_event(
        session,
        stage="Dataset",
        action="Sample Dataset Loaded",
        details=(
            f"{len(dataframe)} records loaded"
            )
        )
    return dataframe