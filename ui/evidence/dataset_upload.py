# ============================================================
# XAIDA 4.0
# ui/dataset_upload.py
# ============================================================

import pandas as pd
import streamlit as st
from pathlib import Path
import logging

from audit.audit_logger import (
    log_audit_event,
)

from orchestration.workflow_engine import (
    transition_to,
    DATASET,
)
from ui.action_dialog import queue_action_message

logger = logging.getLogger(__name__)


class DatasetUploadError(ValueError):
    pass


def render_dataset_upload(session):

    uploader_key = (
        f"dataset_uploader_"
        f"{session.metadata['session_id']}"
    )

    uploaded_file = st.file_uploader(
        "Upload audit dataset",
        type=["xlsx", "csv"],
        key=uploader_key,
    )

    if uploaded_file is None:
        return

    if session.dataset.get(
        "loaded",
        False,
    ):
        return

    try:
        # ==========================================
        # LOAD FILE
        # ==========================================
        file_extension = Path(
            uploaded_file.name
        ).suffix.lower()

        uploaded_file.seek(0)
        if file_extension == ".csv":
            df = pd.read_csv(uploaded_file)
        elif file_extension == ".xlsx":
            df = pd.read_excel(
                uploaded_file
            )
        else:
            raise DatasetUploadError(
                "Unsupported dataset format. Upload a CSV or XLSX file."
            )

        if df.empty or len(df.columns) == 0:
            raise DatasetUploadError(
                "The uploaded dataset contains no records or columns."
            )

        # ==========================================
        # UPDATE SESSION DATASET
        # ==========================================
        session.dataset["dataset_name"] = (
            uploaded_file.name
        )

        session.dataset["dataframe"] = df

        session.dataset["parsing_status"] = "Completed"
        session.dataset["validation_status"] = "Pending"
        session.dataset["validation_results"] = {}

        session.dataset["rows"] = len(df)

        session.dataset["columns"] = (
            len(df.columns)
        )

        session.dataset["loaded"] = True

        session.initialization[
            "dataset_selected"
        ] = True

        session.initialization[
            "dataset_loaded"
        ] = True

        session.initialization[
            "upload_method"
        ] = "file_upload"

        session.initialization[
            "dataset_source"
        ] = uploaded_file.name

        session.initialization[
            "initialization_complete"
        ] = True

        # ==========================================
        # DATASET VERSIONING
        # ==========================================
        session.analysis[
            "dataset_version"
        ] = 1

        session.analysis[
            "analysis_version"
        ] = 0

        session.analysis[
            "analysis_required"
        ] = False

        session.analysis[
            "dataset_versions"
        ] = {
            1: df.copy()
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


        # ==========================================
        # AUDIT LOG
        # ==========================================
        log_audit_event(
            session,
            stage="Dataset",
            action="Dataset Loaded",
            details=(
                f"Dataset={uploaded_file.name}; "
                f"Records={len(df)}; "
                f"Columns={len(df.columns)}"
            )
        )

        # ==========================================
        # WORKFLOW
        # ==========================================
        transition_to(
            session,
            DATASET,
        )

        st.session_state[
            "active_tab"
        ] = "Dataset"

        queue_action_message(
            "Dataset uploaded",
            "The audit dataset was uploaded successfully.",
            "success",
        )

        st.rerun()

    except DatasetUploadError as ex:
        session.dataset["parsing_status"] = "Failed"
        session.dataset["parsing_error"] = str(ex)
        queue_action_message(
            "Dataset upload failed",
            str(ex),
            "error",
        )
    except Exception:
        logger.exception("Dataset upload could not be processed.")
        session.dataset["parsing_status"] = "Failed"
        session.dataset["parsing_error"] = (
            "The file parser could not load the uploaded CSV or XLSX file."
        )

        queue_action_message(
            "Dataset upload failed",
            "The uploaded dataset could not be processed. Check that the file "
            "is a valid CSV or XLSX dataset, then try again.",
            "error",
        )