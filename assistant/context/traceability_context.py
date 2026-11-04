# ===================================
# TRACEABILITY
# ===================================

def build_traceability_context(
    session,
):

    findings_df = (
        session.findings.get(
            "findings_dataframe"
        )
    )

    traceability_records = []

    if findings_df is not None:

        for _, row in (
            findings_df.head(100)
            .iterrows()
        ):

            traceability_records.append(
                {

                    "finding_id":
                    row.get(
                        "Finding ID"
                    ),

                    "finding_status":
                    row.get(
                        "Finding Status"
                    ),

                    "risk_score":
                    row.get(
                        "Risk Score"
                    ),

                    "auditor_assessment":
                    row.get(
                        "Auditor Assessment"
                    ),

                    "dataset_version":
                    session.findings.get(
                        "source_dataset_version"
                    ),

                    "source_record":
                    row.get(
                        "Source Record"
                    ),

                    "record_id":
                    row.get(
                        "Transaction ID",
                        row.get("Record ID"),
                    ),
                }
            )

    return {

        "finding_traceability":
            traceability_records,

        "traceability_available":
        (
            len(
                traceability_records
            ) > 0
        ),
    }