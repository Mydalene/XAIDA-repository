# ============================================================
# XAIDA 4.0
# assistant/action_router.py
# ============================================================

import streamlit as st
import pandas as pd

from orchestration.workflow_engine import (
    transition_to,
    DATA_PREPARATION,
    DUPLICATE_REVIEW,
    ANALYSIS,
    EXPLAINABILITY,
    AUDIT_REVIEW,
    FINDINGS,
    REPORTING,
    AUDIT_COMPLETION,
)

from dataset.version_manager import (
    create_dataset_version,
    get_current_version,
    get_dataset_versions,
)

from dataset.data_preparation_service import (
    run_data_preparation,
)

from analytics.analysis_engine import (
    run_analysis,
)

from dataset.duplicate_resolution import (
    retain_all_duplicates,
    remove_duplicate_copies,
)

from audit.audit_logger import (
    log_audit_event,
)

from assistant.session_manager import (
    reset_session,
)

class ActionRouter:

    def execute(
        self,
        intent,
        session,
        **kwargs,
    ):

        handlers = {

            "complete_initialization":
                self.complete_initialization,
                
            "process_data_preparation":
                self.process_data_preparation, 

            "review_duplicates":
                self.review_duplicates,

            "retain_all_duplicates":
                self.retain_all_duplicates,

            "remove_duplicate_copies":
                self.remove_duplicate_copies,

            "manual_duplicate_review":
                self.manual_duplicate_review,

            "run_analysis":
                self.run_analysis,

            "open_explainability":
                self.open_explainability,

            "open_audit_review":
                self.open_audit_review,

            "confirm_all_flagged_records":
                self.confirm_all_flagged_records,   

            "manual_review":
                self.manual_review,

            "save_review_decisions":
                self.save_review_decisions,

            "open_findings":
                self.open_findings,

            "generate_findings":
                self.generate_findings,
                
            "new_analysis":
                self.new_analysis,

            "continue_to_duplicate_review":
                self.continue_to_duplicate_review,

            "continue_to_analysis":
                self.continue_to_analysis,

            "generate_report":
                self.generate_report,

            "complete_audit":
                self.complete_audit,

        }

        action = handlers.get(intent)

        if action is None:

            return {
                "success": False,
                "message":
                    f"Unknown action: {intent}"
            }

        return action(
            session,
            **kwargs,
        )

    def complete_initialization(
        self,
        session,
        source,
        method,
    ):

        session.initialization[
            "dataset_loaded"
        ] = True

        session.initialization[
            "dataset_source"
        ] = source

        session.initialization[
            "upload_method"
        ] = method

        session.initialization[
            "initialization_complete"
        ] = True

        log_audit_event(
            session,
            stage="Dataset",
            action="Dataset Loaded",
            details=(
                f"Source={source}; "
                f"Method={method}"
            ),
        )

        transition_to(
            session,
            "dataset",
        )

        return {
            "success": True,
        }

    def process_data_preparation(
        self,
        session,
    ):
        run_data_preparation(
            session
        )

        transition_to(
            session,
            DATA_PREPARATION,
        )

        return {
            "success": True,
        }

    def review_duplicates(
        self,
        session,
        **kwargs,
    ):

        transition_to(
            session,
            DUPLICATE_REVIEW,
        )

        st.session_state[
            "active_tab"
        ] = "Duplicate Review"

        log_audit_event(
            session,
            stage="Duplicate Review",
            action="Open Duplicate Review",
            details="Auditor entered duplicate review workflow.",
        )

        return {
            "success": True,
            "message":
                "Duplicate review opened."
        }

    def retain_all_duplicates(
        self,
        session,
        **kwargs,
    ):

        retain_all_duplicates(
            session       
            )

        st.session_state[
            "active_tab"
        ] = "Anomaly Detection"

        log_audit_event(
            session,
            stage="Duplicate Review",
            action="Retain All Duplicates",
            details="All duplicate records retained for analysis.",
        )

        return {
            "success": True,
            "message":
                (
                    "All duplicate "
                    "records retained."
                )
        }

    def remove_duplicate_copies(
        self,
        session,
    ):

        remove_duplicate_copies(
            session
        )

        st.session_state[
            "active_tab"
        ] = "Anomaly Detection"

        log_audit_event(
            session,
            stage="Duplicate Review",
            action="Remove Duplicate Copies",
            details="Duplicate records removed before analysis.",
        )

        return {
            "success": True,
            "message":
                "Duplicate copies removed."
        }

    def manual_duplicate_review(
        self,
        session,
        **kwargs,
    ):
        summary = (
            session.analysis.get(
                "analysis_dataset_summary",
                {}
            )
        )

        summary["strategy"] = (
            "manual_duplicate_review"
        )

        session.analysis[
            "analysis_dataset_summary"
        ] = summary

        session.duplicates[
            "strategy"
        ] = (
            "manual_duplicate_review"
        )

        if (
            session.analysis.get(
                "analysis_dataset"
            )
            is None
        ):
            dataset = (
                session.dataset.get(
                    "dataframe"
                )
            )

            if dataset is not None:
                session.analysis[
                    "analysis_dataset"
                ] = (
                    dataset.copy()
                )

        log_audit_event(
            session,
            stage="Duplicate Review",
            action=(
                "Manual Duplicate Review Selected"
            ),
            details=(
                "Auditor selected manual "
                "duplicate review strategy."
            ),
        )

        return {
            "success": True,
            "message": (
                "Manual duplicate review "
                "enabled."
            ),
        }

    def run_analysis(
        self,
        session,
    ):
        if session.analysis.get(
            "analysis_running",
            False,
        ):
            return {
                "success": False,
                "message":
                    "Analysis already running.",
            }

        if session.analysis.get(
            "analysis_complete",
            False,
        ):
            return {
                "success": True,
                "message":
                    "Analysis already completed.",
            }

        session.analysis[
            "analysis_running"
        ] = True

        try:

            result = run_analysis(
                session
            )

            session.analysis[
                "results"
            ] = result

            session.analysis[
                "analysis_metadata"
            ] = result.get(
                "analysis_metadata",
                {}
            )

            session.analysis[
                "feature_names"
            ] = result.get(
                "feature_names",
                []
            )

            session.analysis[
                "risk_level"
            ] = result.get(
                "risk_level"
            )

            session.analysis[
                "analysis_complete"
            ] = True

            risk_level = result.get(
                "risk_level",
                "Unknown",
            )

            risk_summary = (
                result.get(
                    "risk_summary",
                    {}
                )
            )

            session.analysis[
                "risk_summary"
            ] = risk_summary

            return {
                "success": True,
                "message":
                    "Analysis completed.",
                "result":
                    result,
            }

        finally:

            session.analysis[
                "analysis_running"
            ] = False

    def new_analysis(
        self,
        session,
        **kwargs,
    ):
        new_session = reset_session()

        for key in [
            "dataset_uploader",
            "upload_processed", 
            "active_tab",
            "previous_workflow_stage",
        ]:
            if key in st.session_state:
                del st.session_state[key]

        log_audit_event(
            new_session,
            stage="Dataset",
            action="New Analysis Session",
            details="New XAIDA audit session created.",
        )

        return {
            "success": True,
            "new_session": new_session,
            "message": "New analysis session created.",
        }

    def continue_to_duplicate_review(
        self,
        session,
      **kwargs,
    ):

        transition_to(
            session,
            DUPLICATE_REVIEW,
        )

        st.session_state[
            "active_tab"
        ] = "Duplicate Review"


        log_audit_event(
            session,
            stage="Data Preparation",
            action="Continue To Duplicate Review",
            details="Workflow advanced to duplicate review.",
        )

        return {
            "success": True
        }

    def continue_to_analysis(
        self,
        session,
        **kwargs,
    ):

        dataframe = (
            session.dataset[
                "dataframe"
            ]
        )


        duplicate_count = (
            session.duplicates.get(
                "duplicate_count",
                0,
            )
        )

        log_audit_event(

            session,

            stage="Data Preparation",

            action="Duplicate Check Completed",

            details=(
                f"{len(dataframe)} records reviewed, "
                f"{duplicate_count} duplicates detected"
            ),
        )

        session.analysis[
            "analysis_dataset"
        ] = (
            dataframe.copy()
        )

        transition_to(
            session,
            ANALYSIS,
        )

        return {
            "success": True
        }

    def open_explainability(
        self,
        session,
    ):

        transition_to(
            session,
            EXPLAINABILITY,
        )

        st.session_state[
            "active_tab"
        ] = "Explainability"

        log_audit_event(
            session,
            stage="Explainability",
            action="Explainability Opened",
            details=(
                "Auditor entered "
                "explainability workflow."
            ),
        )

        return {
            "success": True,
        }

    def open_audit_review(
        self,
        session,
    ):

        current_version = get_current_version(session)
        if (
            session.review.get("records") is None
            or session.review.get("review_version") != current_version
        ):

            review_df = (
                get_dataset_versions(
                    session
                ).get(
                    current_version
                )
            )

            if review_df is not None:

                review_df = (
                    review_df.copy()
                )

                if (
                    "Auditor Assessment"
                    not in review_df.columns
                ):
                    review_df[
                        "Auditor Assessment"
                    ] = None

                if (
                    "Auditor Comment"
                    not in review_df.columns
                ):
                    review_df[
                        "Auditor Comment"
                    ] = ""

                session.review[
                    "records"
                ] = review_df
                session.review[
                    "review_version"
                ] = current_version
                
        transition_to(
            session,
            AUDIT_REVIEW,
        )

        st.session_state[
            "active_tab"
        ] = "Audit Review"

        log_audit_event(
            session,
            stage="Audit Review",
            action="Audit Review Opened",
            details=(
                "Auditor entered "
                "Audit review workflow."
            ),
        )

        return {
            "success": True,
        }

    def confirm_all_flagged_records(
        self,
        session,
    ):

        review_df = (
            session.review.get(
                "records"
            )
        )

        if (
            review_df is not None
            and
            not isinstance(
                review_df,
                pd.DataFrame,
            )
        ):
            review_df = None

        if review_df is None:

            current_version = (
                get_current_version(
                    session
                )
            )

            review_df = (
                get_dataset_versions(
                    session
                ).get(
                    current_version
                )
            )

            if review_df is not None:

                review_df = (
                    review_df.copy()
                )

        if review_df is None:

            return {
                "success": False,
                "message":
                    "No review dataset available.",
            }

        if (
            "Auditor Assessment"
            not in review_df.columns
        ):
            review_df[
                "Auditor Assessment"
            ] = None

        review_df.loc[
            review_df[
                "Anomaly Flag"
            ] == True,
            "Auditor Assessment",
        ] = "Confirmed Anomaly"

        session.review[
            "records"
        ] = review_df.copy()

        flagged_count = int(
            review_df["Anomaly Flag"]
            .sum()
        )

        log_audit_event(
            session,
            stage="Audit Review",
            action="Confirm All Flagged Records",
            details=(
                f"{flagged_count} AI-flagged records "
                f"classified as Confirmed Anomaly."
            ),
        )

        return {
            "success": True,
            "message":
                "AI-Flagged records classified.",
        }

    def manual_review(
        self,
        session,
    ):

        session.review[
            "manual_review_mode"
        ] = True

        session.review[
            "bulk_confirmation_complete"
        ] = False

        log_audit_event(
            session,
            stage="Audit Review",
            action="Manual Review",
            details=(
                "Auditor selected "
                "manual review mode."
            ),
        )

        return {
            "success": True,
            "message":
                "Manual review enabled.",
        }

    def save_review_decisions(
        self,
        session,
    ):

        review_df = (
            session.review.get(
                "records"
            )
        )

        if not isinstance(review_df, pd.DataFrame):
            return {
                "success": False,
                "message": "Invalid review dataset.",
            }

        remaining_reviews = len(
            review_df[
                (
                    review_df[
                        "Anomaly Flag"
                    ] == True
                )
                &
                (
                    review_df[
                        "Auditor Assessment"
                    ]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .eq("")
                )
            ]
        )

        if remaining_reviews > 0:

            raise ValueError(
                (
                    f"{remaining_reviews} "
                    "AI-flagged records still "
                    "require review."
                )
            )

        current_version = (
            get_current_version(
                session
            )
        )

        review_df = (
            session.review.get(
                "records"
            )
        )

        if review_df is None:

            return {
                "success": False,
                "message":
                    "No review dataset available.",
            }

        #
        # Save reviewer edits back to
        # dataset versions
        #
        dataset_versions = (
            get_dataset_versions(
                session
            )
        )

        dataset_versions[
            current_version
        ] = review_df.copy()

        session.analysis[
            "dataset_versions"
        ] = dataset_versions

        #
        # Create review version
        #
        new_version = (
            create_dataset_version(
                session=session,
                dataframe=review_df,
                stage="Audit Review",
                action="Save Review Decisions",
            )
        )

        #
        # Lock review
        #
        session.review[
            "audit_review_complete"
        ] = True
        session.review[
            "review_version"
        ] = new_version

        #
        # Disable manual review mode
        #
        session.review[
            "manual_review_mode"
        ] = False

        #
        # Calculate audit entry
        #

        confirmed_anomalies = (
            review_df["Auditor Assessment"]
            .eq("Confirmed Anomaly")
            .sum()
        )

        potential_findings = (
            review_df["Auditor Assessment"]
            .eq("Potential Finding")
            .sum()
        )

        false_positives = (
            review_df["Auditor Assessment"]
            .eq("False Positive")
            .sum()
        )

        requires_investigation = (
            review_df["Auditor Assessment"]
            .eq("Requires Investigation")
            .sum()
        )

        auditor_identified = len(
            review_df[
                (
                    review_df["Anomaly Flag"]
                    == False
                )
                &
                (
                    review_df[
                        "Auditor Assessment"
                    ].isin(
                        [
                            "Confirmed Anomaly",
                            "Potential Finding",
                            "Requires Investigation",
                        ]
                    )
                )
            ]
        )
        #
        # Audit trail
        #
        log_audit_event(
            session,
            stage="Audit Review",
            action="Save Review Decisions",
            details=(
                f"Review completed. "
                f"Version V{new_version} created. "
                f"Confirmed Anomalies={confirmed_anomalies}; "
                f"Potential Findings={potential_findings}; "
                f"False Positives={false_positives}; "
                f"Requires Investigation={requires_investigation}; "
                f"Auditor-Identified={auditor_identified}."
            ),
        )

        return {
            "success": True,
            "message": (
                f"Review decisions saved. "
                f"Dataset version "
                f"V{new_version} created."
            ),
        }

    def open_findings(
        self,
        session,
    ):

        transition_to(
            session,
            FINDINGS,
        )

        st.session_state[
            "active_tab"
        ] = "Findings"

        review_df = (
            session.review.get(
                "records"
            )
        )

        finding_candidates = len(
            review_df[
                review_df[
                    "Auditor Assessment"
                ].isin(
                    [
                        "Confirmed Anomaly",
                        "Potential Finding",
                        "Requires Investigation",
                    ]
                )
            ]
        )

        log_audit_event(
            session,
            stage="Findings",
            action="Findings Opened",
            details=(
                f"Findings stage initiated. "
                f"{finding_candidates} candidate "
                f"findings identified from "
                f"Audit Review."
            ),
        )

        return {
            "success": True,
            "message":
                "Findings opened.",
        }

    def generate_findings(
        self,
        session,
    ):

        review_df = (
            session.review.get(
                "records"
            )
        )

        if review_df is None:

            return {
                "success": False,
                "message":
                    "No review data found.",
            }

        findings_df = review_df[
            review_df[
                "Auditor Assessment"
            ].isin(
                [
                    "Confirmed Anomaly",
                    "Potential Finding",
                    "Requires Investigation",
                ]
            )
        ].copy()
        source_dataset_version = get_current_version(session)
        findings_df["Source Dataset Version"] = (
            source_dataset_version
        )

        findings_df[
            "Finding ID"
        ] = [
            f"F-{i+1:03d}"
            for i in range(
                len(findings_df)
            )
        ]

        findings_df[
            "Finding Status"
        ] = "Open"

        findings_df[
            "Severity"
        ] = "Medium"

        findings_df[
            "Finding Owner"
        ] = ""

        findings_df[
            "Management Response"
        ] = ""

        session.findings[
            "findings_dataframe"
        ] = findings_df
        session.findings[
            "source_dataset_version"
        ] = source_dataset_version

        #
        # Create Findings Version
        #

        findings_version = (
            create_dataset_version(
                session=session,
                dataframe=findings_df,
                stage="Findings",
                action="Generate Findings",
                metadata={
                    "dataset_type": "findings",
                    "source_dataset_version": source_dataset_version,
                    "total_findings":
                        len(
                            findings_df
                        ),
                },
            )
        )
        session.findings[
            "findings_dataset_version"
        ] = findings_version

        auditor_identified = len(
            findings_df[
                (
                    findings_df[
                        "Anomaly Flag"
                    ]
                    == False
                )
            ]
        )

        log_audit_event(
            session,
            stage="Findings",
            action="Generate Findings",
            details=(
                f"Version V{findings_version} "
                f"created. "
                f"Total Findings="
                f"{len(findings_df)}; "
                f"Auditor-Identified="
                f"{auditor_identified}."
            ),
        )

        return {
            "success": True,
            "message":
                f"{len(findings_df)} findings generated.",
        }
    
    def generate_report(
        self,
        session,
    ):

        #
        # Freeze findings register
        #

        session.findings[
            "findings_locked"
        ] = True

        findings_df = (
            session.findings.get(
                "findings_dataframe"
            )
        )

        findings_version = get_current_version(session)
        if findings_df is not None:

            findings_version = (
                create_dataset_version(
                    session=session,
                    dataframe=findings_df,
                    stage="Findings",
                    action="Freeze Findings Register",
                    metadata={
                        "dataset_type": "findings_report",
                        "findings_count":
                            len(
                                findings_df
                            ),
                    },
                )
            )
            session.findings[
                "report_dataset_version"
            ] = findings_version

        log_audit_event(
            session,
            stage="Reporting",
            action="Freeze Findings Register",
            details=(
                f"Version V{findings_version} "
                f"created. "
                f"{len(findings_df) if findings_df is not None else 0} "
                "findings frozen and locked for reporting."
            ),
        )

        session.analysis[
            "report_generated"
        ] = True

        transition_to(session, REPORTING)

        st.session_state[
            "active_tab"
        ] = "Reports"

        session.reporting[
            "pdf_ready"
        ] = True

        session.reporting[
            "excel_ready"
        ] = True

        log_audit_event(
            session,
            stage="Reporting",
            action="Generate Report",
            details="Final audit report generated.",
        )

        return {
            "success": True,
            "message":
                "Audit report generated."
        }

    def complete_audit(
        self,
        session,
    ):
        if not session.reporting.get("pdf_ready", False):
            return {
                "success": False,
                "message": "Generate the audit report before completing the audit.",
            }

        transition_to(session, AUDIT_COMPLETION)
        session.metadata["status"] = "completed"
        log_audit_event(
            session,
            stage="Audit Completion",
            action="Audit Completed",
            details="Audit workflow and reporting are complete.",
        )
        return {
            "success": True,
            "message": "Audit completed.",
        }

router = ActionRouter()

def execute_action(
    intent,
    session,
    **kwargs,
):

    return router.execute(
        intent,
        session,
        **kwargs,
    )
