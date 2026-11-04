# ============================================================
# XAIDA
# exports/pdf_export.py
# ============================================================

from io import BytesIO
from xml.sax.saxutils import escape

import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import (
    getSampleStyleSheet,
)
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    Paragraph,
    Spacer,
    SimpleDocTemplate,
    PageBreak,
    Table,
    TableStyle,
)

from exports.report_generator import (
    build_report_payload,
    report_generation_allowed,
)

def styles():

    theme = getSampleStyleSheet()
    theme["Title"].fontName = "Helvetica-Bold"
    theme["Title"].fontSize = 26
    theme["Title"].leading = 31
    theme["Title"].textColor = colors.HexColor("#15324B")
    theme["Heading2"].fontName = "Helvetica-Bold"
    theme["Heading2"].fontSize = 15
    theme["Heading2"].leading = 19
    theme["Heading2"].textColor = colors.HexColor("#15324B")
    theme["Heading3"].fontName = "Helvetica-Bold"
    theme["Heading3"].textColor = colors.HexColor("#245B75")
    theme["BodyText"].fontName = "Helvetica"
    theme["BodyText"].fontSize = 9
    theme["BodyText"].leading = 13
    theme.add(
        ParagraphStyle(
            name="CoverEyebrow",
            parent=theme["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#167D8D"),
            alignment=TA_LEFT,
            spaceAfter=12,
        )
    )
    theme.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=theme["BodyText"],
            fontSize=12,
            leading=17,
            textColor=colors.HexColor("#526477"),
            spaceAfter=20,
        )
    )
    theme.add(
        ParagraphStyle(
            name="ReportNote",
            parent=theme["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#526477"),
        )
    )
    return theme


def _safe_paragraph(value, style):
    return Paragraph(
        escape(str(value)).replace("\n", "<br/>"),
        style,
    )


def _draw_page_chrome(canvas, doc):
    canvas.saveState()
    page_width, page_height = A4
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
        canvas.setLineWidth(0.6)
        canvas.line(
            doc.leftMargin,
            page_height - 34,
            page_width - doc.rightMargin,
            page_height - 34,
        )
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.HexColor("#526477"))
        canvas.drawString(
            doc.leftMargin,
            page_height - 26,
            "XAIDA  |  AUDIT ANALYTICS REPORT",
        )
    canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
    canvas.setLineWidth(0.6)
    canvas.line(
        doc.leftMargin,
        34,
        page_width - doc.rightMargin,
        34,
    )
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#526477"))
    canvas.drawString(
        doc.leftMargin,
        22,
        "Confidential audit evidence",
    )
    canvas.drawRightString(
        page_width - doc.rightMargin,
        22,
        f"Page {doc.page}",
    )
    canvas.restoreState()


def section_title(
    story,
    theme,
    title,
):

    story.append(
        Spacer(
            1,
            12,
        )
    )

    story.append(
        Paragraph(
            f"<b>{title}</b>",
            theme["Heading2"],
        )
    )

    story.append(
        Spacer(
            1,
            4,
        )
    )

def build_cover_page(
    story,
    theme,
    payload,
):

    dataset = payload[
        "dataset_summary"
    ]

    story.append(Spacer(1, 72))
    story.append(Paragraph("AUDIT EVIDENCE REPORT", theme["CoverEyebrow"]))
    story.append(Paragraph("XAIDA Audit Analytics", theme["Title"]))

    story.append(
        Paragraph(
            "A structured record of analysis, auditor review, findings, "
            "dataset lineage, and workflow activity.",
            theme["CoverSubtitle"],
        )
    )

    cover_rows = [
        ["Report detail", "Value"],
        ["Dataset", str(dataset.get("dataset_name", "Dataset"))],
        ["Records", str(dataset.get("records", 0))],
        ["Columns", str(dataset.get("columns", 0))],
        ["Generated", str(payload.get("generated_at", "Not recorded"))],
    ]
    cover_table = Table(cover_rows, colWidths=[120, 360])
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15324B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#EAF0F5")),
                ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor("#34495E")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(cover_table)
    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            "For authorized audit use. XAIDA provides analytical support; "
            "automated flags are not auditor conclusions or an assurance opinion.",
            theme["ReportNote"],
        )
    )

    story.append(
        PageBreak()
    )

def build_executive_summary(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Executive Summary",
    )

    executive = payload[
        "executive_summary"
    ]

    story.append(
        Paragraph(
            "XAIDA flags are machine-generated screening results; "
            "auditor assessments reflect human review. Counts are descriptive "
            "and do not constitute an assurance opinion.",
            theme["ReportNote"],
        )
    )
    story.append(Spacer(1, 8))

    rows = [

        [
            "Metric",
            "Value",
        ],

        [
            "Total Findings",
            executive[
                "total_findings"
            ],
        ],

        [
            "Confirmed Anomalies",
            executive[
                "confirmed_anomalies"
            ],
        ],

        [
            "Potential Findings",
            executive[
                "potential_findings"
            ],
        ],

        [
            "Requires Investigation",
            executive[
                "requires_investigation"
            ],
        ],

        [
            "False Positives",
            executive[
                "false_positives"
            ],
        ],

        [
            "Auditor‑Identified",
            executive[
                "auditor_identified"
            ],
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            250,
            100,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(
        table
    )

def build_methodology_section(
    story,
    theme,
):

    section_title(
        story,
        theme,
        "Audit Methodology",
    )

    methodology = """

Dataset Upload

Data Preparation

Duplicate Review

Anomaly Detection

Explainability Review

Audit Review

Findings Validation

Report Generation

"""

    story.append(
        Paragraph(
            methodology,
            theme["BodyText"],
        )
    )

def build_dataset_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Dataset Overview",
    )

    dataset = payload[
        "dataset_summary"
    ]

    story.append(
        _safe_paragraph(
            f"Dataset: {dataset.get('dataset_name', 'Dataset')}",
            theme["BodyText"],
        )
    )

    story.append(
        _safe_paragraph(
            f"Records: {dataset.get('records', 0)}",
            theme["BodyText"],
        )
    )

    story.append(
        _safe_paragraph(
            f"Columns: {dataset.get('columns', 0)}",
            theme["BodyText"],
        )
    )

def build_data_preparation_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Data Preparation Summary",
    )

    preparation = payload.get(
        "data_preparation",
        {},
    )

    rows = [

        [
            "Item",
            "Value",
        ],

        [
            "Preparation Strategy",
            str(
                preparation.get(
                    "strategy",
                    "-",
                )
            ),
        ],

        [
            "Missing Values Before",
            str(
                preparation.get(
                    "missing_before",
                    0,
                )
            ),
        ],

        [
            "Missing Values After",
            str(
                preparation.get(
                    "missing_after",
                    0,
                )
            ),
        ],

        [
            "Columns Modified",
            ", ".join(
                preparation.get(
                    "columns_modified",
                    [],
                )
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            200,
            80,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )

def build_duplicate_review_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Duplicate Review Summary",
    )

    duplicate_review = payload.get(
        "duplicate_review",
        {},
    )

    rows = [

        [
            "Item",
            "Value",
        ],

        [
            "Duplicates Detected",
            duplicate_review.get(
                "duplicate_count",
                0,
            ),
        ],

        [
            "Duplicate Groups",
            duplicate_review.get(
                "duplicate_groups",
                0,
            ),
        ],

        [
            "Treatment Applied",
            duplicate_review.get(
                "strategy",
                "-",
            ),
        ],

        [
            "Records Removed",
            duplicate_review.get(
                "records_removed",
                0,
            ),
        ],

        [
            "Duplicates Preserved",
            "Yes",
        ],

    ]

    table = Table(
        rows,
        colWidths=[
            200,
            80,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )

def build_analysis_summary_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "XAIDA-Analysis Summary",
    )

    analysis = payload.get(
        "analysis_summary",
        {},
    )

    rows = [

        [
            "Metric",
            "Value",
        ],

        [
            "Records Analysed",
            analysis.get(
                "records_analysed",
                0,
            ),
        ],

        [
            "Flagged Records",
            analysis.get(
                "flagged_records",
                0,
            ),
        ],

        [
            "Anomaly Rate (%)",
            analysis.get(
                "anomaly_rate",
                0,
            ),
        ],

        [
            "Overall Risk Level",
            analysis.get(
                "risk_level",
                "-",
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            200,
            80,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )

def build_explainability_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "XAIDA-Explainability Summary",
    )

    features = payload.get(
        "explainability_summary",
        [],
    )

    if not features:

        story.append(
            Paragraph(
                (
                    "No explainability "
                    "information available."
                ),
                theme["BodyText"],
            )
        )

        return

    rows = [

        [
            "Rank",
            "Feature",
            "Importance",
        ]
    ]

    for index, feature in enumerate(
        features,
        start=1,
    ):

        rows.append(
            [
                index,
                feature.get(
                    "feature",
                    "",
                ),
                round(
                    float(
                        feature.get(
                            "importance",
                            0,
                        )
                    ),
                    4,
                ),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            60,
            280,
            120,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )



def build_findings_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Findings Summary",
    )

    findings_df = (
        payload[
            "findings_register"
        ]
    )

    if findings_df.empty:

        story.append(
            Paragraph(
                "No findings available.",
                theme["BodyText"],
            )
        )

        return

    summary_rows = [[
        "Finding ID",
        "Assessment",
        "Severity",
        "Status",
    ]]

    for _, row in findings_df.iterrows():

        summary_rows.append([
            str(
                row.get(
                    "Finding ID",
                    "",
                )
            ),
            str(
                row.get(
                    "Auditor Assessment",
                    "",
                )
            ),
            str(
                row.get(
                    "Severity",
                    "",
                )
            ),
            str(
                row.get(
                    "Finding Status",
                    "",
                )
            ),
        ])

    summary_table = Table(
        summary_rows,
        repeatRows=1,
        colWidths=[
            70,
            180,
            90,
            100,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    # ============================================================
    # FINDING DETAILS
    # ============================================================

    story.append(
        PageBreak()
    )

    section_title(
        story,
        theme,
        "Finding Details",
    )

    for _, row in findings_df.iterrows():

        story.append(
            Paragraph(
                f"<b>{escape(str(row.get('Finding ID', '')))}</b>",
                theme["Heading3"],
            )
        )

        #
        # Extract explainability narrative
        #
        explainability = ""

        if (
            "Explainability Narrative"
            in row.index
        ):

            explainability = escape(
                str(
                    row.get(
                        "Explainability Narrative",
                        "",
                    )
                )
            )

            explainability = (
                explainability
                .replace(
                    "cat__",
                    "",
                )
                .replace(
                    "num__",
                    "",
                )
            )

            explainability = (
                explainability
                .replace(
                    ",",
                    "<br/>• "
                )
            )

            if explainability.strip():

                explainability = (
                    "• "
                    + explainability
                )

        #
        # Build detail rows
        #

        detail_rows = [

            [
                "Assessment",
                str(
                    row.get(
                        "Auditor Assessment",
                        "",
                    )
                ),
            ],

            [
                "Severity",
                str(
                    row.get(
                        "Severity",
                        "",
                    )
                ),
            ],

            [
                "Status",
                str(
                    row.get(
                        "Finding Status",
                        "",
                    )
                ),
            ],
        ]

        #
        # Risk Score
        #

        if (
            "Risk Score"
            in row.index
        ):

            detail_rows.append(
                [
                    "Risk Score",
                    str(
                        row.get(
                            "Risk Score",
                            "",
                        )
                    ),
                ]
            )

        #
        # AI Flag
        #

        if (
            "Anomaly Flag"
            in row.index
        ):

            detail_rows.append(
                [
                    "AI Flag",
                    str(
                        row.get(
                            "Anomaly Flag",
                            "",
                        )
                    ),
                ]
            )

        #
        # Explainability Drivers
        #

        if explainability:

            detail_rows.append(
                [
                    Paragraph(
                        "Key Risk Drivers",
                        theme["BodyText"],
                    ),
                    Paragraph(
                        explainability,
                        theme["BodyText"],
                    ),
                ]
            )

        #
        # Auditor Comment
        #

        if (
            "Auditor Comment"
            in row.index
        ):

            detail_rows.append(
                [
                    "Auditor Comment",
                    str(
                        row.get(
                            "Auditor Comment",
                            "",
                        )
                    ),
                ]
            )

        #
        # Management Response
        #

        if (
            "Management Response"
            in row.index
        ):

            detail_rows.append(
                [
                    "Management Response",
                    str(
                        row.get(
                            "Management Response",
                            "",
                        )
                    ),
                ]
            )

        detail_table = Table(
            detail_rows,
            colWidths=[
                140,
                360,
            ],
        )

        detail_table.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        1,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#EAF0F5"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        story.append(
            detail_table
        )

        story.append(
            Spacer(
                1,
                12,
            )
        )

def build_audit_review_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Final Audit Review Summary",
    )

    findings_df = (
        payload[
            "findings_register"
        ]
    )

    review_df = (
        payload[
            "review_dataset"
        ]
    )

    total_reviewed = (
        len(review_df)
        if review_df is not None
        else 0
    )

    confirmed = 0
    potential = 0
    investigation = 0
    false_positive = 0

    if not findings_df.empty:

        confirmed = int(
            findings_df[
                "Auditor Assessment"
            ]
            .eq(
                "Confirmed Anomaly"
            )
            .sum()
        )

        potential = int(
            findings_df[
                "Auditor Assessment"
            ]
            .eq(
                "Potential Finding"
            )
            .sum()
        )

        investigation = int(
            findings_df[
                "Auditor Assessment"
            ]
            .eq(
                "Requires Investigation"
            )
            .sum()
        )

    if (
        review_df is not None
        and
        "Auditor Assessment"
        in review_df.columns
    ):

        false_positive = int(
            review_df[
                "Auditor Assessment"
            ]
            .eq(
                "False Positive"
            )
            .sum()
        )

    rows = [

        [
            "Metric",
            "Value",
        ],

        [
            "Records Reviewed",
            total_reviewed,
        ],

        [
            "Confirmed Anomalies",
            confirmed,
        ],

        [
            "Potential Findings",
            potential,
        ],

        [
            "Requires Investigation",
            investigation,
        ],

        [
            "False Positives",
            false_positive,
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            250,
            120,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )

def build_findings_summary_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Findings Summary",
    )

    summary = (
        payload[
            "findings_summary"
        ]
    )

    rows = [

        [
            "Status",
            "Count",
        ],

        [
            "Open",
            summary.get(
                "open",
                0,
            ),
        ],

        [
            "Under Review",
            summary.get(
                "under_review",
                0,
            ),
        ],

        [
            "Validated",
            summary.get(
                "validated",
                0,
            ),
        ],

        [
            "Dismissed",
            summary.get(
                "dismissed",
                0,
            ),
        ],

        [
            "Resolved",
            summary.get(
                "resolved",
                0,
            ),
        ],
    ]

    table = Table(
        rows,
        colWidths=[
            250,
            120,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )

def build_auditor_identified_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Auditor-Identified Exceptions",
    )

    findings_df = (
        payload[
            "findings_register"
        ]
    )

    if findings_df.empty:

        story.append(
            Paragraph(
                "No auditor-identified exceptions.",
                theme["BodyText"],
            )
        )

        return

    if (
        "Anomaly Flag"
        not in findings_df.columns
    ):

        story.append(
            Paragraph(
                (
                    "Anomaly Flag not "
                    "available."
                ),
                theme["BodyText"],
            )
        )

        return

    auditor_found = (
        findings_df[
            findings_df[
                "Anomaly Flag"
            ]
            == False
        ]
    )

    if auditor_found.empty:

        story.append(
            Paragraph(
                (
                    "No additional "
                    "exceptions were "
                    "identified by the "
                    "auditor."
                ),
                theme["BodyText"],
            )
        )

        return

    rows = [[
        "Finding ID",
        "Assessment",
        "Severity",
        "Status",
    ]]

    for _, row in (
        auditor_found.iterrows()
    ):

        rows.append([
            str(
                row.get(
                    "Finding ID",
                    "",
                )
            ),
            str(
                row.get(
                    "Auditor Assessment",
                    "",
                )
            ),
            str(
                row.get(
                    "Severity",
                    "",
                )
            ),
            str(
                row.get(
                    "Finding Status",
                    "",
                )
            ),
        ])

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[
            70,
            180,
            90,
            100,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
            ]
        )
    )

    story.append(
        table
    )

def build_lineage_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Dataset Lineage",
    )

    lineage = payload.get(
        "dataset_lineage",
        [],
    )

    if not lineage:

        story.append(
            Paragraph(
                (
                    "No dataset lineage "
                    "available."
                ),
                theme["BodyText"],
            )
        )

        return

    rows = [

        [
            "Version",
            "Stage",
            "Action",
            "Records",
        ]
    ]

    for item in lineage:

        rows.append(
            [

                f"V{item['version']}",

                _safe_paragraph(item.get("stage", ""), theme["BodyText"]),

                _safe_paragraph(item.get("action", ""), theme["BodyText"]),

                _safe_paragraph(item.get("records", ""), theme["BodyText"]),

            ]
        )

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[
            60,
            80,
            260,
            80,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "WORDWRAP",
                    (0, 0),
                    (-1, -1),
                    "CJK",
                ),
            ]
        )
    )
    story.append(
        table
    )

def build_audit_trail_section(
    story,
    theme,
    payload,
):

    section_title(
        story,
        theme,
        "Audit Trail",
    )

    audit_trail = payload.get(
        "audit_trail",
        [],
    )

    if not audit_trail:

        story.append(
            Paragraph(
                (
                    "No audit trail "
                    "available."
                ),
                theme["BodyText"],
            )
        )

        return

    rows = [
        [
            "Stage",
            "Action",
            "Details",
        ]
    ]

    for entry in audit_trail:

        rows.append(
            [
                _safe_paragraph(entry.get("stage", ""), theme["BodyText"]),

                _safe_paragraph(entry.get("action", ""), theme["BodyText"]),

                _safe_paragraph(entry.get("details", ""), theme["BodyText"]),
            ]
        )


    table = Table(
        rows,
        colWidths=[
            90,
            120,
            300,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF0F5"),
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "WORDWRAP",
                    (0, 0),
                    (-1, -1),
                    "CJK",
                ),
            ]
        )
    )

    story.append(
        table
    )

def create_pdf_report():

    if not report_generation_allowed():

        raise PermissionError(
            "Report generation locked."
        )

    payload = (
        build_report_payload()
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=48,
        rightMargin=48,
        topMargin=54,
        bottomMargin=50,
        title="XAIDA Audit Analytics Report",
        author="XAIDA",
        subject="Audit evidence and review summary",
    )

    theme = styles()

    story = []

    build_cover_page(
        story,
        theme,
        payload,
    )

    build_executive_summary(
        story,
        theme,
        payload,
    )

    build_methodology_section(
        story,
        theme,
    )

    build_dataset_section(
        story,
        theme,
        payload,
    )

    build_data_preparation_section(
        story,
        theme,
        payload,
    )

    build_duplicate_review_section(
        story,
        theme,
        payload,
    )

    build_analysis_summary_section(
        story,
        theme,
        payload,
    )

    build_audit_review_section(
        story,
        theme,
        payload,
    )

    build_explainability_section(
        story,
        theme,
        payload,
    )

    build_findings_summary_section(
        story,
        theme,
        payload,
    )

    build_auditor_identified_section(
        story,
        theme,
        payload,
    )

    build_findings_section(
        story,
        theme,
        payload,
    )

    build_lineage_section(
        story,
        theme,
        payload,
    )

    build_audit_trail_section(
        story,
        theme,
        payload,
    )

    doc.build(
        story,
        onFirstPage=_draw_page_chrome,
        onLaterPages=_draw_page_chrome,
    )

    buffer.seek(
        0
    )

    return buffer

# ============================================================
# FILE NAME
# ============================================================

def build_pdf_filename():

    return (
        "XAIDA_Audit_Report.pdf"
    )


# ============================================================
# DOWNLOAD BUTTON
# ============================================================

def render_pdf_download():

    if not report_generation_allowed():

        st.info(
            """
Audit report is not yet available.
"""
        )

        return

    try:

        pdf_file = (
            create_pdf_report()
        )

        st.download_button(
            label=
                "📑 Export Audit Report",
            data=pdf_file,
            file_name=
                build_pdf_filename(),
            mime=
                "application/pdf",
            width="stretch",
        )

    except Exception as ex:

        st.error(
            str(ex)
        )


# ============================================================
# STATUS
# ============================================================

def render_pdf_status():

    if report_generation_allowed():

        st.success(
            """
✅ Audit report ready.
"""
        )

    else:

        st.warning(
            """
🔒 Report generation is locked.

Generate Findings and
complete Reporting first.
"""
        )


# ============================================================
# EXPORT PANEL
# ============================================================

def render_pdf_export_panel():

    st.subheader(
        "Audit Report"
    )

    render_pdf_status()

    render_pdf_download()