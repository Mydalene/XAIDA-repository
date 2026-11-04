# ============================================================
# XAIDA 5.0
# ui/evidence/findings_tab.py
# ============================================================

import streamlit as st

from audit.audit_logger import (
    log_audit_event,
)
from ui.evidence.table_download import (
    render_table_download,
)

def render_findings_tab(
    session,
    copilot,
):
    st.subheader("Findings", icon=":material/assignment_late:")
    stage = session.metadata.get(
        "workflow_stage"
    )

    if stage not in [
        "findings",
        "reporting",
        "audit_completion",
    ]:
        st.info(
            "Findings become available after audit review. Complete the review "
            "before continuing.",
            icon=":material/hourglass_top:",
        )
        return

    findings_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    if (
        findings_df is None
        or
        len(findings_df) == 0
    ):
        st.info(
            "No findings have been generated for this audit.",
            icon=":material/inventory_2:",
        )
        return

    source_version = session.findings.get(
        "source_dataset_version"
    )
    findings_version = session.findings.get(
        "findings_dataset_version"
    )
    st.badge(
        f"Findings are based on dataset version "
        f"V{source_version if source_version is not None else 'unknown'}; "
        f"findings dataset version "
        f"V{findings_version if findings_version is not None else 'unknown'}",
        icon=":material/label:",
        color="blue",
    )

    # =====================================================
    # METRICS
    # =====================================================

    open_findings = (
        findings_df[
            "Finding Status"
        ]
        .eq("Open")
        .sum()
    )

    under_review = (
        findings_df[
            "Finding Status"
        ]
        .eq("Under Review")
        .sum()
    )

    validated = (
        findings_df[
            "Finding Status"
        ]
        .eq("Validated")
        .sum()
    )

    resolved = (
        findings_df[
            "Finding Status"
        ]
        .eq("Resolved")
        .sum()
    )

    missed = (
        findings_df[
            "Finding Status"
        ]
        .eq("Missed")
        .sum()
    )

    with st.container(horizontal=True):
        for label, value in (
            ("Open", int(open_findings)),
            ("Under review", int(under_review)),
            ("Validated", int(validated)),
            ("Resolved", int(resolved)),
            ("Missed", int(missed)),
        ):
            with st.container(border=True):
                st.metric(label, value)

    # =====================================================
    # FINDINGS REGISTER
    # =====================================================

    st.subheader("Findings register", icon=":material/table_view:")

    findings_locked = (
        session.findings.get(
            "findings_locked",
            False,
        )
    )

    with st.container(border=True):
        edited_findings = st.data_editor(
            findings_df,
            disabled=findings_locked,
            width="stretch",
            hide_index=True,
            key="findings_editor",
            column_config={
                "Finding Status": st.column_config.SelectboxColumn(
                    "Finding status",
                    options=[
                        "Open",
                        "Under Review",
                        "Validated",
                        "Dismissed",
                        "Resolved",
                    ],
                ),
                "Severity": st.column_config.SelectboxColumn(
                    "Severity",
                    options=[
                        "Low",
                        "Medium",
                        "High",
                        "Critical",
                    ],
                ),
                "Finding Owner": st.column_config.TextColumn(
                    "Finding owner",
                ),
                "Management Response": st.column_config.TextColumn(
                    "Management response",
                    width="large",
                ),
            },
        )

    render_table_download(
        edited_findings,
        "Findings Register",
        "findings_register",
    )

    existing_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    if findings_locked:
        st.success(
            "The report has been generated. The findings register is read-only.",
            icon=":material/lock:",
        )
        
    if (
        existing_df is not None
        and
        not edited_findings.equals(
            existing_df
        )
    ):
        log_audit_event(
            session,
            stage="Findings",
            action="Findings Updated",
            details=(
                "Findings register "
                "updated by auditor."
            ),
        )

    else:
        st.caption(
            "Changes are saved to this audit session. The register locks "
            "when the report is generated."
        )

    session.findings[
        "findings_dataframe"
    ] = (
        edited_findings.copy()
    )

    # =====================================================
    # FINDING SELECTION
    # =====================================================

    st.subheader("Finding details", icon=":material/description:")

    finding_options = (
        edited_findings.index
        .tolist()
    )

    selected_idx = (
        st.selectbox(
            "Select a finding",
            finding_options,
            format_func=lambda x:
            edited_findings.loc[
                x,
                "Finding ID"
            ]
            if "Finding ID"
            in edited_findings.columns
            else f"Finding {x+1}",
        )
    )

    finding = (
        edited_findings.loc[
            selected_idx
        ]
    )

    # =====================================================
    # DETAIL PANEL
    # =====================================================

    info_col, review_col = st.columns(2)
    with info_col:
        with st.container(border=True):
            st.markdown("**Finding information**")

            if "Finding ID" in finding.index:
                st.write(f"Finding ID: {finding['Finding ID']}")

            if "Risk Score" in finding.index:
                st.write(f"Risk score: {finding['Risk Score']}")

            if "Severity" in finding.index:
                st.write(f"Severity: {finding['Severity']}")

            if "Finding Status" in finding.index:
                st.write(f"Status: {finding['Finding Status']}")

    with review_col:
        with st.container(border=True):
            st.markdown("**Review information**")

            if "Auditor Assessment" in finding.index:
                st.write(f"Assessment: {finding['Auditor Assessment']}")

            if "Finding Owner" in finding.index:
                st.write(f"Owner: {finding['Finding Owner']}")

            st.write(
                "Source version: "
                f"V{finding.get('Source Dataset Version', 'unknown')}"
            )

    auditor_comment = (
        finding.get(
            "Auditor Comment",
            "",
        )
    )

    management_response = (
        finding.get(
            "Management Response",
            "",
        )
    )

    with st.container(horizontal=True):
        with st.container(border=True):
            st.markdown("**Auditor comment**")
            st.write(auditor_comment or "No auditor comment.")
        with st.container(border=True):
            st.markdown("**Management response**")
            st.write(management_response or "No management response.")

    st.markdown("**Source record**")

    excluded_columns = [
        "Finding ID",
        "Finding Status",
        "Severity",
        "Finding Owner",
        "Management Response",
    ]

    record_snapshot = (
        finding.drop(
            labels=[
                c
                for c
                in excluded_columns
                if c in finding.index
            ]
        )
    )

    source_record_df = record_snapshot.to_frame()
    render_table_download(
        source_record_df,
        f"Source Record for {finding.get('Finding ID', selected_idx)}",
        f"finding_source_record_{selected_idx}",
    )
    with st.container(border=True):
        st.dataframe(
            source_record_df,
            width="stretch",
            hide_index=True,
        )