from dataset.imputation_rules import DEFAULT_IMPUTATION_RULES


# ===================================
# METHODOLOGY
# ===================================

def build_methodology_context(
    session,
    risk_summary,
):
    return {
        
        "threshold_method":
            "Dynamic Quantile Threshold",

        "risk_level_methodology":
        """
        Low Risk:
        < 2% anomaly rate

        Moderate Risk:
        2% to < 5%

        High Risk:
        >= 5%
        """,

        "transaction_explanation_method":
        """
        For flagged records, SHAP is applied to a separately fitted
        Isolation Forest using the transformed feature matrix. The
        displayed explanation lists the three features with the largest
        absolute SHAP values for that record. It identifies influential
        features, not whether each feature increased or decreased risk.
        """,

        "explainability_methodology":
        """
        SHAP is calculated for flagged rows using an Isolation Forest
        explainer. Global drivers are ranked by mean absolute SHAP value;
        each record shows its three largest absolute contributors.

        Higher importance scores indicate
        greater influence on the Isolation Forest output being explained,
        not necessarily the weighted ensemble risk score.

        High importance does not necessarily
        indicate fraud, error or control
        failure.
        """,

        # ===================================
        # METHODOLOGY
        # ===================================

        "total_transactions":
            session.dataset.get(
                "rows",
                0,
            ),

        "anomaly_rate_calculation":
        (
            f"{risk_summary.get('flagged_transactions', 0)} "
            f"/ "
            f"{session.dataset.get('rows', 0)} "
            f"x 100"
        ),

        "anomaly_methodology":
        """
        Transactions are assigned risk scores
        during anomaly detection.

        Transactions with risk scores greater
        than the calculated anomaly threshold
        are flagged as anomalous.

        The anomaly rate is calculated as:

        Flagged Transactions
        /
        Total Transactions
        x 100
        """,

        "duplicate_detection_methodology":
        """
        XAIDA performs exact duplicate detection.

        All columns are compared.

        Matching records are grouped into
        Duplicate Groups and assigned
        Case IDs (DUP-xxxx).

        Detected duplicates are initially
        marked as Pending Review.
        """,

        "null_value_classification_methodology":
        """
        Null values are classified into:

        • Business Valid

        • Unexpected

        Imputation rules are applied only
        when missing values are present.
        """,


        "feature_engineering_methodology":
        """
        Implemented preprocessing conditionally creates Days_To_Due and
        Days_To_Payment when the required date columns exist; decomposes
        datetime columns into year, month, quarter, weekday and day;
        converts booleans to integers; adds Log_Amount when Amount exists;
        fills remaining numeric nulls with column medians, categorical nulls
        with Unknown, and remaining nulls with zero; standard-scales numeric
        columns and one-hot encodes categorical columns. PCA is defined as a
        utility but is not called by the active analysis path.
        """,

        "feature_engineering_output_policy":
        (
            "Feature engineering is performed on an internal analysis "
            "feature matrix. It does not add engineered columns to the "
            "displayed or versioned source dataset. Dataset preparation "
            "operations such as documented imputation or duplicate removal "
            "are separate and may create dataset versions."
        ),

        # ===================================
        # AVAILABLE DUPLICATE STRATEGIES
        # ===================================

        "available_duplicate_strategies":
        [
            {
                "name":
                    "Retain All Duplicates",
                "purpose":
                    "Preserve all duplicate records."
            },
            {
                "name":
                    "Remove Duplicate Copies",
                "purpose":
                    "Remove redundant duplicate copies while retaining one representative record."
            },
            {
                "name":
                    "Manual Duplicate Review",
                "purpose":
                    "Allow auditors to review duplicates individually before removal."
            },
        ],

        "default_imputation_rules":
            DEFAULT_IMPUTATION_RULES,

        "imputation_methodology":
        """
        Data preparation applies a column-specific imputation rule when
        configured; otherwise numeric columns use the median, categorical
        columns use the mode, and datetime columns are retained. Applied
        strategies and record counts are available in the imputation log.
        Actual session rules and outcomes take precedence over these defaults.
        """,

    }