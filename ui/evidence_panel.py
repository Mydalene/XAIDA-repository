# ============================================================
# XAIDA 4.0
# ui/evidence_panel.py
# ============================================================

import streamlit as st
from audit.services.audit_readiness import (
    calculate_audit_readiness,
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

from ui.evidence.audit_review_tab import (
    render_audit_review_tab,
)

def render_evidence_panel(
    session,
    vertex_ai_assistant,
):
    stage = session.metadata.get(
        "workflow_stage",
        "initialization",
    )
    readiness = calculate_audit_readiness(session)
    st.subheader("Audit Evidence")

    readiness_status = readiness["status"]
    status_styles = {
        "Audit Ready": ("green", ":material/check_circle:"),
        "Needs Review": ("orange", ":material/warning:"),
        "Not Ready": ("red", ":material/error:"),
    }
    status_color, status_icon = status_styles.get(
        readiness_status,
        ("gray", ":material/info:"),
    )
    readiness_score = float(readiness["score"])
    explained_records = readiness.get("explained_records", 0)
    flagged_records = readiness.get("flagged_records", 0)
    remaining_reviews = readiness.get("remaining_reviews", 0)
    explainability_summary = (
        f"{explained_records} of {flagged_records} flagged records explained"
        if flagged_records
        else "No flagged records to explain"
    )

    with st.container(border=True):
        st.markdown("#### Audit readiness")
        st.badge(
            readiness_status,
            icon=status_icon,
            color=status_color,
        )

        st.progress(
            readiness_score / 100,
            text=f"{readiness_score:.0f}% readiness",
        )
        detail_col, review_col = st.columns(2)
        with detail_col:
            st.caption(explainability_summary)
        with review_col:
            st.caption(f"{remaining_reviews} audit reviews outstanding")

        with st.expander("Readiness score breakdown"):
            for item in readiness["breakdown"]:
                status_icon = (
                    ":material/check_circle:"
                    if item["complete"]
                    else ":material/pending:"
                )
                st.write(
                    f"{status_icon} **{item['step']}** — "
                    f"{item['earned']} / {item['weight']}%"
                    f"{'' if item['complete'] else ' · Incomplete'}"
                )
            st.caption(
                "Upload 20% · preparation 30% (20% when duplicates are "
                "found) · duplicate review 10% when needed · analysis 50%."
            )
            if not readiness["audit_review_complete"]:
                st.caption(
                    "Audit review is tracked separately and is required "
                    "before the audit is marked ready."
                )
            elif remaining_reviews:
                st.caption(
                    f"{remaining_reviews} flagged records still need review."
                )

    stage_tab_map = {
        "initialization":
            "Dataset",

        "dataset":
            "Dataset",

        "data_preparation":
            "Data Processing",

        "duplicate_review":
            "Duplicate Review",

        "analysis":
            "Anomaly Detection",

        "explainability":
            "Explainability",

        "audit_review":
            "Audit Review",

        "findings":
            "Findings",

        "reporting":
            "Reports",

        "audit_completion":
            "Reports",
    }

    default_tab = (
        stage_tab_map.get(
            stage,
            "Dataset",
        )
    )

    #
    # Auto-activate tab ONLY when
    # workflow stage changes
    #
    previous_stage = (
        st.session_state.get(
            "previous_workflow_stage"
        )
    )

    if "active_tab" not in st.session_state:

        st.session_state[
            "active_tab"
        ] = default_tab

    if previous_stage is None:

        st.session_state[
            "previous_workflow_stage"
        ] = stage

    elif previous_stage != stage:

        st.session_state[
            "active_tab"
        ] = default_tab

        st.session_state[
            "previous_workflow_stage"
        ] = stage
        
       
    tab_options = [
        "Dataset",
        "Data Processing",
        "Duplicate Review",
        "Anomaly Detection",
        "Explainability",
        "Audit Review",
        "Findings",
        "Reports",
        "Lineage",
        "Audit Trail",
    ]
    selected_tab = (
        st.segmented_control(
            label="Evidence stages",
            label_visibility="collapsed",
            options=tab_options,
            selection_mode="single",
            key="active_tab",
            width="stretch",
        )
    )
    session.metadata["active_evidence_tab"] = selected_tab

    findings_dataframe = session.findings.get("findings_dataframe")
    has_findings = (
        findings_dataframe is not None
        and not findings_dataframe.empty
    )
    analysis_complete = bool(
        session.analysis.get("analysis_complete", False)
    )
    explainability_complete = (
        analysis_complete
        and (
            readiness.get("flagged_records", 0) == 0
            or readiness.get("explainability_coverage", 0) >= 100
        )
    )
    duplicate_review_not_needed = (
        session.dataset.get("data_preparation_complete", False)
        and session.duplicates.get("duplicate_count", 0) == 0
    )

    stage_statuses = {
        "Dataset": (
            "Complete"
            if session.dataset.get("loaded", False)
            else (
                "In progress"
                if stage in {"initialization", "dataset"}
                else "Pending"
            )
        ),
        "Data Processing": (
            "Complete"
            if session.dataset.get("data_preparation_complete", False)
            else (
                "In progress"
                if stage == "data_preparation"
                else "Pending"
            )
        ),
        "Duplicate Review": (
            "Not required"
            if duplicate_review_not_needed
            else (
                "Complete"
                if session.duplicates.get("duplicate_review_complete", False)
                else (
                    "In progress"
                    if stage == "duplicate_review"
                    else "Pending"
                )
            )
        ),
        "Anomaly Detection": (
            "Complete"
            if analysis_complete
            else (
                "In progress"
                if stage == "analysis"
                else "Pending"
            )
        ),
        "Explainability": (
            "Complete"
            if explainability_complete
            else (
                "In progress"
                if stage == "explainability"
                else "Pending"
            )
        ),
        "Audit Review": (
            "Complete"
            if session.review.get("audit_review_complete", False)
            else (
                "In progress"
                if stage == "audit_review"
                else "Pending"
            )
        ),
        "Findings": (
            "Complete"
            if session.findings.get("findings_locked", False)
            else (
                "In progress"
                if stage == "findings"
                else ("Available" if has_findings else "Pending")
            )
        ),
        "Reports": (
            "Complete"
            if stage == "audit_completion"
            else (
                "Complete"
                if session.analysis.get("report_generated", False)
                else (
                    "In progress"
                    if stage == "reporting"
                    else "Pending"
                )
            )
        ),
    }
    status_styles = {
        "Complete": ("green", "check_circle"),
        "In progress": ("blue", "pending"),
        "Pending": ("gray", "schedule"),
        "Not required": ("gray", "remove_circle"),
        "Available": ("blue", "visibility"),
        "Evidence": ("violet", "description"),
    }
    with st.container(horizontal=True, gap="small"):
        for tab_name in tab_options:
            status = stage_statuses.get(
                tab_name,
                "Evidence" if tab_name in {"Lineage", "Audit Trail"} else None,
            )
            if status is None:
                continue
            color, icon = status_styles[status]
            st.caption(
                f":{color}-badge[:material/{icon}: {tab_name}: {status}]"
            )

    # =====================================================
    # DATASET
    # =====================================================

    if selected_tab == "Dataset":

        render_dataset_tab(
            session
        )

    # =====================================================
    # PREPARATION
    # =====================================================

    elif selected_tab == "Data Processing":

        render_preparation_tab(
            session
        )

    # =====================================================
    # DUPLICATE REVIEW
    # =====================================================

    elif (
        selected_tab
        == "Duplicate Review"
    ):

        render_duplicate_tab(
            session
        )

    # =====================================================
    # ANALYSIS
    # =====================================================

    elif (
        selected_tab
        == "Anomaly Detection"
    ):

        render_analysis_tab(
            session
        )

    # =====================================================
    # EXPLAINABILITY
    # =====================================================

    elif (
        selected_tab
        == "Explainability"
    ):

        render_explainability_tab(
            session
        )

    # =====================================================
    # AUDIT REVIEW
    # =====================================================

    elif (
        selected_tab
        == "Audit Review"
    ):
        render_audit_review_tab(
            session
        )

    # =====================================================
    # FINDINGS
    # =====================================================

    elif (
        selected_tab
        == "Findings"
    ):

        render_findings_tab(session)

    # =====================================================
    # REPORTS
    # =====================================================

    elif selected_tab == "Reports":

        render_reports_tab(
            session
        )

    # =====================================================
    # LINEAGE
    # =====================================================

    elif selected_tab == "Lineage":

        render_lineage_tab(
            session
        )

    # =====================================================
    # AUDIT TRAIL
    # =====================================================

    elif (
        selected_tab
        == "Audit Trail"
    ):

        render_audit_tab(
            session
        )