# ============================================================
# XAIDA 4.0
# dataset/missing_value_service.py
# ============================================================


from dataset.imputation_rules import (
    DEFAULT_IMPUTATION_RULES,
)

from datetime import datetime


def profile_missing_values(
    dataframe,
):

    missing_summary = (
        dataframe
        .isnull()
        .sum()
        .reset_index()
    )

    missing_summary.columns = [
        "Column",
        "Missing Count",
    ]

    missing_summary[
        "Missing Percent"
    ] = (
        missing_summary[
            "Missing Count"
        ]
        / len(dataframe)
        * 100
    ).round(2)

    return missing_summary


def classify_missing_values(
    dataframe,
):

    business_valid = []
    unexpected = []

    if (
        "PaidDate"
        in dataframe.columns
        and
        "Status"
        in dataframe.columns
    ):

        valid_paiddate = (
            dataframe[
                (
                    dataframe[
                        "PaidDate"
                    ].isna()
                )
                &
                (
                    dataframe[
                        "Status"
                    ].astype(str)
                    .str.lower()
                    .isin(
                        [
                            "open",
                            "partial",
                        ]
                    )
                )
            ]
        )

        business_valid.append(
            {
                "column":
                    "PaidDate",
                "records":
                    len(valid_paiddate),
                "reason":
                    (
                        "Invoice not fully paid"
                    ),
            }
        )

    for column in dataframe.columns:

        null_count = (
            dataframe[
                column
            ]
            .isna()
            .sum()
        )

        if (
            null_count > 0
            and
            column != "PaidDate"
        ):

            unexpected.append(
                {
                    "column":
                        column,
                    "records":
                        null_count,
                }
            )

    return {
        "business_valid":
            business_valid,
        "unexpected":
            unexpected,
    }

def apply_imputation_rule(
    dataframe,
    column,
    rule,
):

    strategy = rule.get(
        "strategy"
    )

    if strategy == "retain":

        return dataframe

    if strategy == "median":

        dataframe[column] = (
            dataframe[column]
            .fillna(
                dataframe[column]
                .median()
            )
        )

        return dataframe

    if strategy == "mean":

        dataframe[column] = (
            dataframe[column]
            .fillna(
                dataframe[column]
                .mean()
            )
        )

        return dataframe

    if strategy == "mode":

        dataframe[column] = (
            dataframe[column]
            .fillna(
                dataframe[column]
                .mode()[0]
            )
        )

        return dataframe

    if strategy == "constant":

        dataframe[column] = (
            dataframe[column]
            .fillna(
                rule.get(
                    "value"
                )
            )
        )

        return dataframe

    return dataframe


def prepare_dataset_for_analysis(
    dataframe,
    rules=None,
):

    if rules is None:

        rules = (
            DEFAULT_IMPUTATION_RULES
        )

    prepared = (
        dataframe.copy()
    )

    treatment_log = []

    for column in prepared.columns:

        missing_count = (
            prepared[column]
            .isna()
            .sum()
        )

        if missing_count == 0:

            continue

        rule = (
            rules[
                "columns"
            ].get(
                column
            )
        )

        if rule is None:

            if str(
                prepared[column].dtype
            ).startswith(
                "datetime"
            ):

                rule = (
                    rules[
                        "datetime"
                    ]
                )

            elif (
                prepared[column]
                .dtype
                .kind
                in "if"
            ):

                rule = (
                    rules[
                        "numeric"
                    ]
                )

            else:

                rule = (
                    rules[
                        "categorical"
                    ]
                )

        prepared = (
            apply_imputation_rule(
                prepared,
                column,
                rule,
            )
        )

        treatment_log.append(
            {
                "column": column,
                "strategy": rule["strategy"],
                "records": missing_count,
                "reason": rule.get(
                    "reason",
                    (
                        "The configured policy retains these missing values; "
                        "no more specific business rationale is recorded."
                        if rule["strategy"] == "retain"
                        else (
                            f"The configured {rule['strategy']} rule was "
                            "applied; no more specific rationale is recorded."
                        )
                    ),
                ),
                "dataset_modified":
                    rule["strategy"] != "retain",
                "timestamp":
                    datetime.now().isoformat(),
            }
        )

    return (
        prepared,
        treatment_log,
    )
