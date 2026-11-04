# ============================================================
# XAIDA 4.0
# ui/evidence/reports_tab.py
# ============================================================

import streamlit as st

from exports.pdf_export import (
    render_pdf_download,
)

from exports.excel_export import (
    render_excel_download,
)

def render_reports_tab(
    session,
):
    stage = (
        session.metadata.get(
            "workflow_stage"
        )
    )

    if not session.analysis.get(
        "report_generated",
        False,
    ):
        st.info(
            "The audit report is not ready yet. "
            f"Current workflow stage: "
            f"{str(stage or 'unknown').replace('_', ' ').title()}. "
            "Generate the report from the sidebar when the findings stage "
            "is complete.",
            icon=":material/hourglass_top:",
        )
        return

    st.subheader("Audit reports", icon=":material/description:")

    with st.container(border=True):
        st.markdown("**Download report files**")
        st.caption(
            "Choose a format to save a copy of the completed audit report."
        )
        render_pdf_download()
        render_excel_download(session)
