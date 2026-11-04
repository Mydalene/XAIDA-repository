# ===================================
# REPORTING
# ===================================

def build_reporting_context(
    session,
):

    reporting = getattr(session, "reporting", {})

    report_generated = (
        session.analysis.get(
            "report_generated",
            False,
        )
    )
    dataset_versions = session.analysis.get(
        "dataset_versions",
        {},
    ) or {}
    version_metadata = session.analysis.get(
        "dataset_version_metadata",
        {},
    ) or {}

    version_sheets = []
    for version, dataframe in dataset_versions.items():
        if dataframe is None:
            continue
        metadata = version_metadata.get(version, {})
        stage = str(
            metadata.get(
                "stage",
                "Dataset" if version == 1 else "Unknown",
            )
        ).replace(" ", "_")
        version_sheets.append(
            {
                "version": f"V{version}",
                "sheet_name": f"V{version}_{stage}"[:31],
                "records": len(dataframe),
                "columns": len(dataframe.columns),
            }
        )

    findings_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    total_findings = 0

    if findings_df is not None:

        total_findings = len(
            findings_df
        )

    return {

        # ==============================
        # REPORT STATUS
        # ==============================

        "anonymous_survey_status":
            "An optional anonymous XAIDA evaluation survey is being prepared. "
            "The survey link is not available yet. Survey responses are "
            "separate from audit findings, reports, and Vertex AI assistant "
            "evaluation records.",

        "report_generated":
            report_generated,

        "report_available":
            report_generated,

        "report_dataset_version":
            session.findings.get("report_dataset_version"),

        "report_source_dataset_version":
            session.findings.get("source_dataset_version"),

        "findings_locked":
            session.findings.get("findings_locked", False),

        # ==============================
        # REPORT SUMMARY
        # ==============================

        "total_findings":
            total_findings,

        "executive_summary":
            reporting.get("executive_summary"),

        "report_recommendations":
            reporting.get("recommendations", []),

        "validated_findings":
            (
                session.findings.get(
                    "validated",
                    [],
                )
            ),

        "open_findings":
            (
                session.findings.get(
                    "open",
                    [],
                )
            ),

        # ==============================
        # REPORT CONTENT
        # ==============================

        "executive_summary_available":
            report_generated,

        "findings_summary_available":
            report_generated,

        "recommendations_available":
            report_generated,

        # ==============================
        # REPORT EXPORTS
        # ==============================

        "pdf_export_available":
            report_generated,

        "excel_export_available":
            report_generated,

        "excel_report_includes_dataset_versions":
            bool(version_sheets),

        "excel_report_dataset_version_sheets":
            version_sheets,

        "excel_report_download_available":
            bool(report_generated and reporting.get("excel_ready", False)),

        "evidence_tables_downloadable":
            True,

        "evidence_table_download_format":
            "CSV",

        "evidence_table_download_scope":
            "Every table displayed in the Audit Evidence panel, including "
            "interactive dataset and review tables.",

        # ==============================
        # REPORTING NAVIGATION
        # ==============================

        "report_sections":
        [
            "Executive Summary",
            "Findings Summary",
            "Detailed Findings",
            "Recommendations",
            "Audit Evidence",
            "Export Options",
        ],

        "reporting_workflow_steps":
        [
            "Review Findings Summary",
            "Review Detailed Findings",
            "Review Recommendations",
            "Generate Report",
            "Export PDF",
            "Export Excel",
        ],
    }