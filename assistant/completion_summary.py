# ============================================================
# XAIDA 4.0
# assistant/completion_summary.py
# ============================================================

def build_completion_summary(
    session,
):

    rows = session.dataset.get(
        "rows",
        0,
    )

    duplicate_count = session.duplicates.get(
        "duplicate_count",
        0,
    )

    strategy = (
        session.analysis.get(
            "analysis_dataset_summary",
            {}
        ).get(
            "strategy",
            "Not Selected",
        )
    )

    results = session.analysis.get(
        "results",
        {}
    )

    risk_summary = results.get(
        "risk_summary",
        {}
    )

    flagged_transactions = (
        risk_summary.get(
            "flagged_transactions",
            0,
        )
    )

    risk_level = (
        risk_summary.get(
            "risk_level",
            "Unknown",
        )
    )

    versions = len(
        session.analysis.get(
            "dataset_version_metadata",
            {}
        )
    )

    validated_findings = len(
        session.findings.get(
            "validated",
            [],
        )
    )

    open_findings = len(
        session.findings.get(
            "open",
            [],
        )
    )

    review_metrics = session.review.get(
        "audit_review_metrics",
        {},
    )

    return f"""
# Audit Workflow Completed

The audit has been closed and its final report is ready.

## Audit snapshot

• Dataset records reviewed: {rows}
• Duplicate records identified: {duplicate_count}
• Duplicate strategy: {strategy}
• AI-flagged records: {review_metrics.get("ai_flagged_records", "Not recorded")}
• Auditor-confirmed anomalies: {review_metrics.get("confirmed_anomalies", "Not recorded")}
• Potential findings: {review_metrics.get("potential_findings", "Not recorded")}
• False positives: {review_metrics.get("false_positives", "Not recorded")}
• Records requiring investigation: {review_metrics.get("requires_investigation", "Not recorded")}
• Flagged records awaiting review: {review_metrics.get("remaining_reviews", "Not recorded")}

## Findings and reporting

• Validated findings: {validated_findings}
• Open findings: {open_findings}
• Flagged transactions: {flagged_transactions}
• Risk indicator: {risk_level}
• Dataset versions: {versions}
• Final audit report: Ready

Thank you for using XAIDA. Auditor judgment remains authoritative. You can
continue to review this session's evidence or ask XAIDA questions; AI output
should be checked against the audit record.

"""