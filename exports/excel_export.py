# ============================================================
# CREATE AUDIT EVIDENCE WORKBOOK
# ============================================================

from io import BytesIO
from datetime import datetime

import streamlit as st
import pandas as pd


def create_analysis_workbook(
    session,
):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter",
        engine_kwargs={
            "options": {
                "strings_to_formulas": False,
            },
        },
    ) as writer:

        workbook = writer.book

        _write_summary_sheet(writer, session)

        # ====================================================
        # REVIEW DATASET
        # ====================================================

        review_df = (
            session.review.get(
                "records"
            )
        )

        if review_df is not None:

            review_df.to_excel(
                writer,
                sheet_name=
                    "Review_Dataset",
                index=False,
            )

            _autosize_sheet(
                writer,
                "Review_Dataset",
                review_df,
            )

        # ====================================================
        # DUPLICATE RECORDS
        # ====================================================

        duplicate_df = (
            session.duplicates.get(
                "removed_duplicate_records"
            )
        )

        if (
            duplicate_df is not None
            and
            not duplicate_df.empty
        ):

            duplicate_df.to_excel(
                writer,
                sheet_name=
                    "Duplicate_Records",
                index=False,
            )

            _autosize_sheet(
                writer,
                "Duplicate_Records",
                duplicate_df,
            )

        # ====================================================
        # FINDINGS REGISTER
        # ====================================================

        findings_df = (
            session.findings.get(
                "findings_dataframe"
            )
        )

        if (
            findings_df is not None
            and
            not findings_df.empty
        ):

            findings_df.to_excel(
                writer,
                sheet_name=
                    "Findings_Register",
                index=False,
            )

            _autosize_sheet(
                writer,
                "Findings_Register",
                findings_df,
            )

        # ====================================================
        # FALSE POSITIVES
        # ====================================================

        if (
            review_df is not None
            and
            "Auditor Assessment"
            in review_df.columns
        ):

            false_positive_df = (
                review_df[
                    review_df[
                        "Auditor Assessment"
                    ]
                    ==
                    "False Positive"
                ]
                .copy()
            )

            if not false_positive_df.empty:

                false_positive_df.to_excel(
                    writer,
                    sheet_name=
                        "False_Positives",
                    index=False,
                )

                _autosize_sheet(
                    writer,
                    "False_Positives",
                    false_positive_df,
                )

        # ====================================================
        # DATASET LINEAGE
        # ====================================================

        versions = (
            session.analysis.get(
                "dataset_versions",
                {},
            )
        )

        metadata = (
            session.analysis.get(
                "dataset_version_metadata",
                {},
            )
        )

        lineage_rows = []

        for version, df in versions.items():

            info = metadata.get(
                version,
                {},
            )

            lineage_rows.append(
                {
                    "Version":
                        f"V{version}",

                    "Stage":
                        info.get(
                            "stage",
                            (
                                "Dataset"
                                if version == 1
                                else "Unknown"
                            ),
                        ),

                    "Action":
                        info.get(
                            "action",
                            (
                                "Dataset Upload"
                                if version == 1
                                else "Unknown"
                            ),
                        ),

                    "Records":
                        len(df),

                    "Columns":
                        len(df.columns),
                }
            )

        lineage_df = pd.DataFrame(
            lineage_rows
        )

        lineage_df.to_excel(
            writer,
            sheet_name=
                "Dataset_Lineage",
            index=False,
        )

        _autosize_sheet(
            writer,
            "Dataset_Lineage",
            lineage_df,
        )

        # ====================================================
        # AUDIT TRAIL
        # ====================================================

        audit_df = pd.DataFrame(
            session.audit_log
        )

        audit_df.to_excel(
            writer,
            sheet_name=
                "Audit_Trail",
            index=False,
        )

        _autosize_sheet(
            writer,
            "Audit_Trail",
            audit_df,
        )

        # ====================================================
        # ALL DATASET VERSIONS
        # ====================================================

        for version, df in versions.items():

            info = metadata.get(
                version,
                {},
            )

            stage = (
                info.get(
                    "stage",
                    (
                        "Dataset"
                        if version == 1
                        else "Unknown"
                    ),
                )
                .replace(
                    " ",
                    "_",
                )
            )

            sheet_name = (
                f"V{version}_{stage}"
            )[:31]

            df.to_excel(
                writer,
                sheet_name=
                    sheet_name,
                index=False,
            )

            _autosize_sheet(
                writer,
                sheet_name,
                df,
            )

    output.seek(
        0
    )

    return output


# ============================================================
# AUTO-SIZE WORKSHEET
# ============================================================

def _autosize_sheet(
    writer,
    sheet_name,
    dataframe,
):

    if dataframe is None:
        return

    worksheet = (
        writer.sheets[
            sheet_name
        ]
    )
    header_format = writer.book.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#15324B",
            "text_wrap": True,
            "valign": "vcenter",
            "border": 0,
        }
    )
    worksheet.set_row(0, 30, header_format)
    worksheet.freeze_panes(1, 0)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 0)

    if not dataframe.empty and len(dataframe.columns):
        worksheet.autofilter(
            0,
            0,
            len(dataframe),
            len(dataframe.columns) - 1,
        )

    for idx, col in enumerate(
        dataframe.columns
    ):

        try:

            max_len = max(
                dataframe[
                    col
                ]
                .astype(str)
                .map(len)
                .max(),
                len(str(col)),
            )

        except Exception:

            max_len = len(
                str(col)
            )

        worksheet.set_column(
            idx,
            idx,
            min(
                max_len + 2,
                60,
            ),
        )


def _write_summary_sheet(writer, session):
    worksheet = writer.book.add_worksheet("Audit_Summary")
    writer.sheets["Audit_Summary"] = worksheet
    workbook = writer.book
    title_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 20,
            "font_color": "#FFFFFF",
            "bg_color": "#15324B",
            "valign": "vcenter",
        }
    )
    subtitle_format = workbook.add_format(
        {
            "font_size": 10,
            "font_color": "#526477",
            "text_wrap": True,
            "valign": "vcenter",
        }
    )
    section_format = workbook.add_format(
        {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#167D8D",
        }
    )
    label_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#EAF0F5",
            "valign": "top",
        }
    )
    value_format = workbook.add_format(
        {
            "text_wrap": True,
            "valign": "top",
        }
    )

    worksheet.merge_range("A1:C1", "XAIDA Audit Evidence Report", title_format)
    worksheet.set_row(0, 34)
    worksheet.merge_range(
        "A2:C2",
        "Summary of the current audit session and its generated evidence. "
        "Review findings and source evidence before relying on or sharing this file.",
        subtitle_format,
    )
    worksheet.set_row(1, 34)
    worksheet.set_column("A:A", 28)
    worksheet.set_column("B:B", 34)
    worksheet.set_column("C:C", 22)
    worksheet.freeze_panes(3, 0)

    dataset = session.dataset
    dataframe = dataset.get("dataframe")
    findings_df = session.findings.get("findings_dataframe")
    review_df = session.review.get("records")
    versions = session.analysis.get("dataset_versions", {})

    details = [
        ("Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Dataset", dataset.get("dataset_name", "Dataset")),
        ("Workflow stage", session.metadata.get("workflow_stage", "Not recorded")),
        ("Source records", len(dataframe) if dataframe is not None else 0),
        (
            "Source columns",
            len(dataframe.columns) if dataframe is not None else 0,
        ),
        ("Dataset versions", len(versions)),
    ]

    assessments = {}
    if findings_df is not None and "Auditor Assessment" in findings_df.columns:
        assessments = findings_df["Auditor Assessment"].value_counts().to_dict()

    review_count = len(review_df) if review_df is not None else 0
    audit_metrics = [
        ("Records in review dataset", review_count),
        (
            "Findings in register",
            len(findings_df) if findings_df is not None else 0,
        ),
        ("Confirmed anomalies", assessments.get("Confirmed Anomaly", 0)),
        ("Potential findings", assessments.get("Potential Finding", 0)),
        (
            "Requires investigation",
            assessments.get("Requires Investigation", 0),
        ),
        ("False positives", assessments.get("False Positive", 0)),
    ]

    row = 3
    for section, items in (
        ("Report details", details),
        ("Audit review snapshot", audit_metrics),
    ):
        worksheet.merge_range(row, 0, row, 2, section, section_format)
        row += 1
        for label, value in items:
            worksheet.write_string(row, 0, str(label), label_format)
            if isinstance(value, (int, float)):
                worksheet.write_number(row, 1, value, value_format)
            else:
                worksheet.write_string(row, 1, str(value), value_format)
            row += 1
        row += 1

    worksheet.merge_range(
        row,
        0,
        row,
        2,
        "Interpretation",
        section_format,
    )
    worksheet.merge_range(
        row + 1,
        0,
        row + 2,
        2,
        "Anomaly flags are machine-generated screening results, not auditor "
        "conclusions. Auditor assessments reflect human review. Validate the "
        "underlying evidence and apply your organization's controls to this export.",
        subtitle_format,
    )
    worksheet.set_row(row + 1, 30)
    worksheet.set_row(row + 2, 22)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 1)

# ============================================================
# FILE NAME
# ============================================================

def build_excel_filename():

    return (
        "XAIDA_Audit_Evidence.xlsx"
    )


# ============================================================
# DOWNLOAD BUTTON
# ============================================================

def render_excel_download(
    session,
):  

    if not session.reporting.get(
        "excel_ready",
        False,
    ):

        st.info(
            """
Audit evidence workbook
is not yet available.
"""
        )

        return

    try:

        workbook = (
            create_analysis_workbook(
                session
            )
        )

        st.download_button(
            label=
                "📊 Export Audit Evidence",
            data=workbook,
            file_name=
                build_excel_filename(),
            mime=(
                "application/vnd."
                "openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    except Exception as ex:

        st.error(
            f"Excel export failed: {ex}"
        )