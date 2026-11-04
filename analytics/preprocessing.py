import numpy as np
import pandas as pd

from sklearn.compose import (
    ColumnTransformer,
    make_column_selector,
)

from sklearn.preprocessing import (
    StandardScaler,
    OneHotEncoder,
)

# ============================================================
# FEATURE TRANSFORMATION
# ============================================================

def transform_features(
    dataframe,
):

    df = dataframe.copy()

    # ========================================================
    # BOOLEAN COLUMNS
    # ========================================================

    bool_columns = df.select_dtypes(
        include=["bool"]
    ).columns

    for col in bool_columns:

        df[col] = (
            df[col]
            .astype(int)
        )

    # ========================================================
    # DATE DIFFERENCE FEATURES
    # ========================================================

    date_pairs = [

        (
            "InvoiceDate",
            "DueDate",
            "Days_To_Due",
        ),

        (
            "InvoiceDate",
            "PaidDate",
            "Days_To_Payment",
        ),
    ]

    for start_col, end_col, feature_name in date_pairs:

        if (
            start_col in df.columns
            and end_col in df.columns
        ):

            start_dates = pd.to_datetime(
                df[start_col],
                errors="coerce",
            )

            end_dates = pd.to_datetime(
                df[end_col],
                errors="coerce",
            )

            df[feature_name] = (
                end_dates
                - start_dates
            ).dt.days

            df[feature_name] = (
                df[feature_name]
                .fillna(-1)
            )

    # ========================================================
    # DATE FEATURES
    # ========================================================

    date_columns = df.select_dtypes(
        include=[
            "datetime64[ns]",
            "datetime64",
        ]
    ).columns

    for col in date_columns:

        date_series = pd.to_datetime(
            df[col],
            errors="coerce",
        )

        df[f"{col}_Year"] = (
            date_series.dt.year.fillna(0)
        )

        df[f"{col}_Month"] = (
            date_series.dt.month.fillna(0)
        )

        df[f"{col}_Quarter"] = (
            date_series.dt.quarter.fillna(0)
        )

        df[f"{col}_Weekday"] = (
            date_series.dt.weekday.fillna(0)
        )

        df[f"{col}_Day"] = (
            date_series.dt.day.fillna(0)
        )

        df.drop(
            columns=[col],
            inplace=True,
        )

    # ========================================================
    # AMOUNT FEATURES
    # ========================================================

    if "Amount" in df.columns:

        df["Log_Amount"] = np.log1p(
            df["Amount"].clip(lower=0)
        )

    # ========================================================
    # FINAL NULL HANDLING
    # ========================================================

    num_cols = df.select_dtypes(
        include=[np.number]
    ).columns

    df[num_cols] = (
        df[num_cols]
        .fillna(
            df[num_cols].median()
        )
    )

    cat_cols = df.select_dtypes(
        include=[
            "object",
            "category",
        ]
    ).columns

    df[cat_cols] = (
        df[cat_cols]
        .fillna("Unknown")
    )

    df.fillna(
        0,
        inplace=True,
    )

    # ========================================================
    # COLUMN TRANSFORMER
    # ========================================================

    transformer = ColumnTransformer(

        transformers=[

            (
                "num",
                StandardScaler(),
                make_column_selector(
                    dtype_include=np.number,
                ),
            ),

            (
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                make_column_selector(
                    dtype_include=[
                        "object",
                        "category",
                    ],
                ),
            ),
        ],

        remainder="drop",
    )

    features = (
        transformer.fit_transform(
            df
        )
    )

    feature_names = (
        transformer.get_feature_names_out()
    )

    return (
        features,
        feature_names,
    )

