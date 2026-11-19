def summarize_finding_status(
    findings_dataframe,
    status,
    fallback_records=None,
):
    if (
        findings_dataframe is not None
        and "Finding Status" in findings_dataframe.columns
    ):
        matching_records = findings_dataframe.loc[
            findings_dataframe["Finding Status"]
            .eq(status)
            .fillna(False)
        ]
        return (
            len(matching_records),
            matching_records.head(50).to_dict("records"),
        )

    records = list(fallback_records or [])
    return len(records), records[:50]
