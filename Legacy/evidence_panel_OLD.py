# ============================================================
# XAIDA 4.0
# ui/evidence_panel.py
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from exports.pdf_export import (
    render_pdf_download,
)

from exports.excel_export import (
    render_excel_download,
)

from audit.audit_logger import (
    log_audit_event,
)

from dataset.version_manager import (
    create_dataset_version,
    get_current_version,
    get_dataset_versions,
    get_version_metadata,
)

from audit.change_tracker import (
    get_change_log,
)

from ui.evidence.findings_tab import (
    render_findings_tab,
)

from ui.evidence.lineage_tab import (
    render_lineage_tab,
)

from ui.evidence.audit_tab import (
    render_audit_tab,
)

from ui.evidence.reports_tab import (
    render_reports_tab,
)

from ui.evidence.duplicate_tab import (
    render_duplicate_tab,
)

from ui.evidence.preparation_tab import (
    render_preparation_tab,
)

from ui.evidence.dataset_tab import (
    render_dataset_tab,
)

from ui.evidence.analysis_tab import (
    render_analysis_tab,
)

from ui.evidence.explainability_tab import (
    render_explainability_tab,
)

def render_evidence_panel(
    session,
):

    st.subheader(
        "Audit Evidence"
    )

    dataset_tab, prep_tab, duplicate_tab, anomaly_tab, explainability_tab, findings_tab, lineage_tab, reports_tab, audit_tab = st.tabs(
        [
            "Dataset",
            "Preparation",
            "Duplicate Review",
            "Anomaly Detection",
            "Explainability",
            "Findings",
            "Lineage",
            "Reports",
            "Audit Trail",
        ]
    )

    with dataset_tab:
        render_dataset_tab(
            session
        )

    with duplicate_tab:
        render_duplicate_tab(
            session
        )             

    with prep_tab:
        render_preparation_tab(
            session
        )

    with anomaly_tab:
        render_analysis_tab(
            session
        )

    with explainability_tab:
        render_explainability_tab(
            session
        )

    with findings_tab:
        render_findings_tab(
            session
        )

    with lineage_tab:
        render_lineage_tab(
            session
        )

    with reports_tab:
        render_reports_tab(
            session
        )  

    with audit_tab:
        render_audit_tab(
            session
        )