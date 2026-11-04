# ============================================================
# XAIDA
# core/validation.py
# ============================================================

import pandas as pd

# ============================================================
# VALIDATION RESULT TEMPLATE
# ============================================================

def _empty_result():

    return {
        "valid": False,
        "rows": 0,
        "columns": 0,
        "column_names": [],
        "duplicate_columns": [],
        "missing_values": 0,
        "missing_percentage": 0.0,
        "numeric_columns": 0,
        "categorical_columns": 0,
        "messages": [],
    }


# ============================================================
# REQUIRED CHECKS
# ============================================================

def validate_dataset(
    df: pd.DataFrame
):
    """
    Validate uploaded dataset.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    dict
        Validation summary.
    """

    result = _empty_result()

    # --------------------------------------------------------
    # DATAFRAME EXISTS
    # --------------------------------------------------------

    if df is None:

        result["messages"].append(
            "Dataset is None."
        )

        return result

    # --------------------------------------------------------
    # DATAFRAME TYPE
    # --------------------------------------------------------

    if not isinstance(
        df,
        pd.DataFrame,
    ):

        result["messages"].append(
            "Input is not a pandas DataFrame."
        )

        return result

    # --------------------------------------------------------
    # EMPTY DATASET
    # --------------------------------------------------------

    if df.empty:

        result["messages"].append(
            "Dataset is empty."
        )

        return result

    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    rows, columns = df.shape

    result["rows"] = rows
    result["columns"] = columns

    # --------------------------------------------------------
    # COLUMN NAMES
    # --------------------------------------------------------

    result["column_names"] = (
        df.columns.tolist()
    )

    # --------------------------------------------------------
    # DUPLICATE COLUMN NAMES
    # --------------------------------------------------------

    duplicate_columns = list(
        df.columns[
            df.columns.duplicated()
        ]
    )

    result["duplicate_columns"] = (
        duplicate_columns
    )

    if duplicate_columns:

        result["messages"].append(
            f"Duplicate column names found: "
            f"{', '.join(duplicate_columns)}"
        )

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    total_missing = int(
        df.isna().sum().sum()
    )

    result["missing_values"] = (
        total_missing
    )

    total_cells = rows * columns

    if total_cells > 0:

        result["missing_percentage"] = round(
            (
                total_missing
                / total_cells
            )
            * 100,
            2,
        )

    # --------------------------------------------------------
    # COLUMN TYPES
    # --------------------------------------------------------

    numeric_columns = list(
        df.select_dtypes(
            include="number"
        ).columns
    )

    categorical_columns = list(
        df.select_dtypes(
            exclude="number"
        ).columns
    )

    result["numeric_columns"] = (
        len(numeric_columns)
    )

    result["categorical_columns"] = (
        len(categorical_columns)
    )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    if rows < 10:

        result["messages"].append(
            "Very small dataset detected."
        )

    if columns < 2:

        result["messages"].append(
            "Very few columns detected."
        )

    if total_missing > 0:

        result["messages"].append(
            f"{total_missing:,} missing values detected."
        )

    # --------------------------------------------------------
    # VALIDITY
    # --------------------------------------------------------

    result["valid"] = True

    if duplicate_columns:

        result["valid"] = False

    return result


# ============================================================
# SUMMARY TEXT
# ============================================================

def build_validation_summary(
    validation_result: dict
):
    """
    Produce a UI-friendly summary.
    """

    if not validation_result["valid"]:

        return (
            "Dataset validation failed."
        )

    return (
        f"Rows: {validation_result['rows']:,} | "
        f"Columns: {validation_result['columns']:,} | "
        f"Missing Values: "
        f"{validation_result['missing_values']:,}"
    )


# ============================================================
# DATASET PROFILE
# ============================================================

def generate_dataset_profile(
    df: pd.DataFrame
):
    """
    Generate additional metadata
    useful for dashboard display.
    """

    profile = {

        "rows": len(df),

        "columns": len(df.columns),

        "numeric_columns": len(
            df.select_dtypes(
                include="number"
            ).columns
        ),

        "categorical_columns": len(
            df.select_dtypes(
                exclude="number"
            ).columns
        ),

        "memory_usage_mb": round(
            (
                df.memory_usage(
                    deep=True
                ).sum()
                / 1024
                / 1024
            ),
            2,
        ),
    }

    return profile


# ============================================================
# DATASET SUITABILITY
# ============================================================

def is_ready_for_analysis(
    validation_result: dict
):
    """
    Determine whether dataset is
    suitable for XAIDA analysis.
    """

    return bool(
        validation_result["valid"]
    )