def _record_identifier_values(dataframe, mask):
    identifier_position = next(
        (
            position
            for name in (
                "transactionid",
                "recordid",
                "invoiceid",
                "caseid",
                "id",
            )
            for position, column in enumerate(dataframe.columns)
            if "".join(
                character
                for character in str(column).lower()
                if character.isalnum()
            ) == name
        ),
        None,
    )
    identifier_column = (
        dataframe.columns[identifier_position]
        if identifier_position is not None
        else None
    )
    rows = []
    for position in range(len(dataframe)):
        if not bool(mask.iloc[position]):
            continue
        identifier = (
            dataframe.iloc[position, identifier_position]
            if identifier_position is not None
            else None
        )
        if hasattr(identifier, "item"):
            identifier = identifier.item()
        source_index = dataframe.index[position]
        if hasattr(source_index, "item"):
            source_index = source_index.item()
        rows.append(
            {
                "record_id_field": identifier_column,
                "record_id": identifier,
                "source_row_position": position + 1,
                "source_index": source_index,
            }
        )
    return rows


def build_data_preparation_context(
    session,
    include_record_identifiers=False,
):

    classification = session.dataset.get(
        "missing_classification",
        {},
    ) or {}
    imputation_log = session.dataset.get(
        "imputation_log",
        [],
    ) or []
    treatment_details = []
    for entry in imputation_log:
        detail = dict(entry)
        if not detail.get("reason"):
            if detail.get("strategy") == "retain":
                detail["reason"] = (
                    "The configured imputation rule retains this column's "
                    "missing values. Check missing classification and "
                    "column-specific policy for the business reason."
                )
            else:
                detail["reason"] = (
                    "The configured imputation strategy was applied; no "
                    "more specific per-column rationale was recorded."
                )
        treatment_details.append(detail)

    dataframe = session.dataset.get("dataframe")
    missing_record_identifiers = []
    if include_record_identifiers and dataframe is not None:
        for column_position, column in enumerate(dataframe.columns):
            missing_mask = dataframe.iloc[:, column_position].isna()
            missing_count = int(missing_mask.sum())
            if missing_count:
                missing_record_identifiers.append(
                    {
                        "column": column,
                        "missing_record_count": missing_count,
                        "record_identifiers": _record_identifier_values(
                            dataframe,
                            missing_mask,
                        ),
                    }
                )

    return {

        "missing_summary":
        (
            session.dataset.get(
                "missing_summary"
            )
            .to_dict("records")
            if session.dataset.get(
                "missing_summary"
            ) is not None
            else []
        ),

        "missing_classification":
            classification,

        "missing_record_identifiers":
            missing_record_identifiers,

        "missing_value_retention_reasons": [
            {
                "column": item.get("column"),
                "records": item.get("records"),
                "reason": item.get("reason"),
            }
            for item in classification.get("business_valid", [])
        ],

        "imputation_log":
            treatment_details,

        "imputation_rules":
            session.dataset.get(
                "imputation_rules",
                {},
            ),
    }