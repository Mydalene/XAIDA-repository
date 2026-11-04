from assistant.conversation_manager import (
    clear_conversation,
)

from assistant.session_manager import (
    create_default_analysis_state,
    create_default_duplicates_state,
    create_default_explainability_state,
    create_default_findings_state,
    create_default_reporting_state,
)

def reset_analysis_run(
    session
):

    # =====================================
    # ANALYSIS
    # =====================================

    session.analysis = (
        create_default_analysis_state()
    )
    # =====================================
    # FINDINGS
    # =====================================

    session.findings = (
        create_default_findings_state()
    )

    # =====================================
    # EXPLAINABILITY
    # =====================================

    session.explainability = (
        create_default_explainability_state()
    )

    # =====================================
    # REPORTING
    # =====================================

    session.reporting = (
        create_default_reporting_state()
    )

    # =====================================
    # DUPLICATES
    # =====================================

    session.duplicates = (
        create_default_duplicates_state()
    )

    clear_conversation(
        session
    )

def reset_analysis_artifacts(
    session,
):
    reset_analysis_run(
        session
    )