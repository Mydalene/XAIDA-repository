# ============================================================
# XAIDA 4.0
# ui/evidence/audit_tab.py
# ============================================================

import pandas as pd
import streamlit as st

from ui.evidence.table_download import (
    dataframe_for_streamlit,
    render_table_download,
)


def render_audit_tab(
    session,
):
    st.subheader("Audit trail", icon=":material/history:")
    audit_df = pd.DataFrame(session.audit_log)
    if audit_df.empty:
        st.info(
            "Audit events will appear here as work is completed.",
            icon=":material/info:",
        )
        return

    with st.container(border=True):
        st.caption(
            "A chronological record of actions performed in this audit session."
        )
        render_table_download(
            audit_df,
            "Audit Trail",
            "audit_trail",
        )
        st.dataframe(
            dataframe_for_streamlit(audit_df),
            width="stretch",
            hide_index=True,
        )