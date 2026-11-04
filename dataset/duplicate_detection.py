
def detect_duplicates(
    df
):

    duplicate_records = df[
        df.duplicated(
            keep=False
        )
    ].copy()

    duplicate_records[
        "Original Index"
    ] = duplicate_records.index

    if duplicate_records.empty:

        return duplicate_records

    duplicate_records[
        "Duplicate Group"
    ] = (
        duplicate_records
        .groupby(
            list(df.columns),
            dropna=False,
        )
        .ngroup()
        + 1
    )

    duplicate_records[
        "Case ID"
    ] = (
        "DUP-"
        + duplicate_records[
            "Duplicate Group"
        ]
        .astype(str)
        .str.zfill(4)
    )

    duplicate_records[
        "Status"
    ] = (
        "Pending Review"
    )

    return duplicate_records
