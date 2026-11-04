# ===================================
# AUDIT TRAIL
# ===================================

def build_trail_context(
    session,
):

    trail = (
        session.audit_log
        if session.audit_log
        else []
    )

    return {

        # ==========================
        # AUDIT EVENTS
        # ==========================

        "audit_entry_count":
        len(
            trail
        ),

        "audit_entries":
        trail,

        "recent_audit_events":
        (
            trail[-10:]
            if trail
            else []
        ),

        # ==========================
        # TIMELINE
        # ==========================

        "latest_audit_event":
        (
            trail[-1]
            if trail
            else None
        ),

        "audit_timeline":
        trail,

        # ==========================
        # NAVIGATION
        # ==========================

        "audit_trail_sections":
        [
            "Audit Trail",
            "Recent Audit Events",
            "Audit Timeline",
        ],

        "audit_trail_workflow_steps":
        [
            "Review Recent Events",
            "Review Event History",
            "Review Audit Timeline",
            "Review Workflow Progression",
        ],
    }