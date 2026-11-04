def build_dataset_context(
    session,
):

    df = session.dataset.get(
        "dataframe"
    )

    return {

        # DATASET

        "dataset_name":
        session.dataset.get(
            "dataset_name"
        ),

        "rows":
        session.dataset.get(
            "rows"
        ),

        "columns":
        session.dataset.get(
            "columns"
        ),

        "dataset_version":
        session.analysis.get(
            "dataset_version",
            session.dataset.get("dataset_version"),
        ),

        "dataset_version_history":
            session.analysis.get("dataset_version_metadata", {}),

        "data_preparation_complete":
            session.dataset.get("data_preparation_complete", False),

        "dataset_summary":
        session.dataset.get(
            "dataset_summary"
        ),

        "dataset_profile":
            session.dataset.get("profile", {}),

        "feature_count":
        (
            len(df.columns)
            if df is not None
            else 0
        ),

        "column_names":
        (
            list(df.columns)
            if df is not None
            else []
        ),

        "column_types":
        (
            {
                col: str(dtype)
                for col, dtype
                in df.dtypes.items()
            }
            if df is not None
            else {}
        ),

        "dataset_preview":
        (
            df.head(10)
              .to_dict(
                  "records"
              )
            if df is not None
            else []
        ),

        "feature_definitions":
        (
            [
                {
                    "column": col,
                    "type": str(dtype),
                }
                for col, dtype
                in df.dtypes.items()
            ]
            if df is not None
            else []
        ),

        "parsing_status":
        session.dataset.get(
            "parsing_status",
            "Not Available",
        ),

        "parsing_error":
            session.dataset.get("parsing_error"),

        "validation_status":
        session.dataset.get(
            "validation_status",
            "Not Available",
        ),

        "validation_results":
            session.dataset.get("validation_results", {}),
    }