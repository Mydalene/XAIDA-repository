import re

import numpy as np
import pandas as pd


# ===================================
# ANALYSIS
# ===================================

_RECORD_IDENTIFIER_NAMES = {
    "transactionid",
    "recordid",
    "invoiceid",
    "caseid",
    "id",
}


def _query_matches_identifier(query, value):
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        if np.isfinite(value) and float(value).is_integer():
            value = str(int(value))
        else:
            value = str(value)
    else:
        value = str(value).strip()
    if not value:
        return False
    return re.search(
        rf"(?<![\w.]){re.escape(value)}(?![\w.])",
        query,
        flags=re.IGNORECASE,
    ) is not None


def _requested_record_risk_scores(analysis_dataframe, user_message):
    if (
        analysis_dataframe is None
        or "Risk Score" not in analysis_dataframe.columns
        or not user_message
        or not re.search(r"\b(risk|score)\b", user_message, re.IGNORECASE)
    ):
        return [], 0

    identifier_columns = [
        column
        for column in analysis_dataframe.columns
        if "".join(
            character
            for character in str(column).lower()
            if character.isalnum()
        ) in _RECORD_IDENTIFIER_NAMES
    ]
    matches = []
    match_count = 0

    for source_record, row in analysis_dataframe.iterrows():
        matched_identifiers = {
            str(column): row[column]
            for column in identifier_columns
            if _query_matches_identifier(user_message, row[column])
        }
        if _query_matches_identifier(user_message, source_record):
            matched_identifiers["source_record"] = source_record
        if not matched_identifiers:
            continue

        match_count += 1
        if len(matches) < 50:
            matches.append(
                {
                    "source_record": source_record,
                    "record_identifiers": matched_identifiers,
                    "risk_score": float(row["Risk Score"]),
                    "anomaly_flag": bool(
                        row["Anomaly Flag"]
                        if "Anomaly Flag" in analysis_dataframe.columns
                        else False
                    ),
                }
            )

    return matches, match_count


def build_analysis_context(
    session,
    risk_summary,
    user_message=None,
):

    analysis_metadata = (
        session.analysis.get(
            "analysis_metadata",
            {}
        ) or {}
    )

    results = (
        session.analysis.get(
            "results"
        ) or {}
    )
    version_metadata = session.analysis.get(
        "dataset_version_metadata",
        {},
    ) or {}
    anomaly_dataset_version = next(
        (
            version
            for version, metadata in reversed(
                list(version_metadata.items())
            )
            if metadata.get("dataset_type") == "anomaly"
            or "anomaly dataset"
            in str(metadata.get("action", "")).lower()
        ),
        None,
    )

    analysis_dataframe = results.get("analysis_dataframe")
    if analysis_dataframe is None:
        analysis_dataframe = session.analysis.get("analysis_dataset")

    risk_score_histogram = []
    histogram_totals = {
        "normal": 0,
        "anomaly": 0,
    }
    if (
        analysis_dataframe is not None
        and "Risk Score" in analysis_dataframe.columns
    ):
        scores = analysis_dataframe["Risk Score"].to_numpy(dtype=float)
        valid_scores = np.isfinite(scores)
        scores = scores[valid_scores]
        if len(scores):
            edges = np.histogram_bin_edges(scores, bins=30)
            flags = (
                analysis_dataframe["Anomaly Flag"]
                .fillna(False)
                .astype(bool)
                .to_numpy()[valid_scores]
                if "Anomaly Flag" in analysis_dataframe.columns
                else np.zeros(len(scores), dtype=bool)
            )
            normal_counts, _ = np.histogram(
                scores[~flags],
                bins=edges,
            )
            anomaly_counts, _ = np.histogram(
                scores[flags],
                bins=edges,
            )
            histogram_totals = {
                "normal": int(normal_counts.sum()),
                "anomaly": int(anomaly_counts.sum()),
            }
            risk_score_histogram = [
                {
                    "risk_score_min": float(edges[index]),
                    "risk_score_max": float(edges[index + 1]),
                    "normal_records": int(normal_counts[index]),
                    "anomaly_records": int(anomaly_counts[index]),
                }
                for index in range(len(edges) - 1)
            ]

    flagged_transaction_details = []
    all_record_risk_scores = []
    requested_record_risk_scores, requested_record_risk_score_match_count = (
        _requested_record_risk_scores(
            analysis_dataframe,
            user_message,
        )
    )
    if analysis_dataframe is not None:
        if "Risk Score" in analysis_dataframe.columns:
            all_record_risk_scores = [
                {
                    "source_record": int(index),
                    "risk_score": float(score),
                    "anomaly_flag": bool(
                        analysis_dataframe.loc[index, "Anomaly Flag"]
                        if "Anomaly Flag" in analysis_dataframe.columns
                        else False
                    ),
                }
                for index, score in analysis_dataframe["Risk Score"].items()
            ]

        if "Anomaly Flag" in analysis_dataframe.columns:
            flagged_dataframe = analysis_dataframe[
                analysis_dataframe["Anomaly Flag"].fillna(False).astype(bool)
            ].copy()
            flagged_dataframe.insert(
                0,
                "Source Record",
                flagged_dataframe.index,
            )
            explanation_by_record = results.get("explanation_by_record", {})
            if explanation_by_record:
                flagged_dataframe["Key Drivers"] = [
                    explanation_by_record.get(index)
                    for index in flagged_dataframe.index
                ]
            flagged_transaction_details = (
                flagged_dataframe.head(50).to_dict("records")
            )

    return {

        # ===================================
        # ANALYSIS STATUS
        # ===================================

        "analysis_required":
        (
            session.analysis.get(
                "analysis_required",
                False,
            )
        ),

        "analysis_complete":
        (
            session.analysis.get(
                "analysis_complete",
                False,
            )
        ),

        "risk_level":
        (
            risk_summary.get(
                "risk_level",
                session.analysis.get(
                    "risk_level"
                ),
            )
        ),

        "flagged_transactions":
        (
            risk_summary.get(
                "flagged_transactions",
                0,
            )
        ),

        "high_risk_transactions":
        (
            risk_summary.get(
                "high_risk_transactions",
                0,
            )
        ),

        "flag_rate":
        (
            risk_summary.get(
                "flag_rate",
                0,
            )
        ),

        # ===================================
        # ANALYSIS ENGINE
        # ===================================

        "analysis_engine":
            "Ensemble Detection",

        "ensemble_members":
        [
            "Isolation Forest",
            "K-Means Distance Scoring",
            "MLP Autoencoder",
        ],

        "ensemble_weights":
        {
            "Isolation Forest": "40%",
            "K-Means": "20%",
            "Autoencoder": "40%",
        },

        "threshold":
        (
            results.get(
                "threshold"
            )
        ),

        "anomaly_dataset_version":
            anomaly_dataset_version,

        "risk_score_histogram":
        {
            "bin_count": len(risk_score_histogram),
            "normal_records": histogram_totals["normal"],
            "anomaly_records": histogram_totals["anomaly"],
            "bins": risk_score_histogram,
        },

        "flagged_transaction_details":
            flagged_transaction_details,

        "all_record_risk_scores":
            all_record_risk_scores[:200],

        "requested_record_risk_scores":
            requested_record_risk_scores,

        "requested_record_risk_score_match_count":
            requested_record_risk_score_match_count,

        "flagged_transaction_details_limit":
            min(len(flagged_transaction_details), 50),

        "feature_diagnostics":
            session.analysis.get("feature_diagnostics"),

        "threshold_description":
        """
        The anomaly threshold is calculated
        using the upper quantile of the
        ensemble risk score distribution.

        Current contamination level:
        5%.
        """,

        # ===================================
        # ANALYSIS METADATA
        # ===================================

        "dataset_version":
        (
            analysis_metadata.get(
                "dataset_version"
            )
        ),

        "model":
        (
            analysis_metadata.get(
                "model"
            )
        ),

        "model_version":
        (
            analysis_metadata.get(
                "model_version"
            )
        ),

        "feature_count":
        (
            analysis_metadata.get(
                "feature_count"
            )
        ),

        # ===================================
        # ANALYSIS NAVIGATION
        # ===================================

        "analysis_sections":
        [
            "Analysis Input Dataset",
            "Analysis Output Dataset",
            "Anomaly Detection Details",
            "Summary Results",
            "Top Risk Transactions",
        ],

        "analysis_workflow_steps":
        [
            "Review Analysis Input Dataset",
            "Review Risk Score Distribution",
            "Review Analysis Output Dataset",
            "Review Anomaly Detection Details",
            "Review Highest Risk Transactions",
            "Open Explainability",
        ],

        "analysis_navigation_help":
        """
        1. Review Analysis Input Dataset
        2. Review Risk Score Distribution
        3. Review Analysis Output Dataset
        4. Review Detection Details
        5. Review Highest Risk Transactions
        6. Open Explainability
        """,

        # ===================================
        # ANALYSIS STATISTICS
        # ===================================

        "analysis_record_count":
        (
            len(
                session.analysis.get(
                    "analysis_dataset"
                )
            )
            if
            session.analysis.get(
                "analysis_dataset"
            ) is not None
            else 0
        ),

        "flagged_transaction_count":
        (
            risk_summary.get(
                "flagged_transactions",
                0,
            )
        ),

        "high_risk_transaction_count":
        (
            risk_summary.get(
                "high_risk_transactions",
                0,
            )
        ),

        # ===================================
        # DUPLICATE REVIEW TRACEABILITY
        # ===================================

        "duplicate_review_complete":
        (
            session.duplicates.get(
                "duplicate_review_complete",
                False,
            )
        ),

        "duplicate_strategy":
        (
            session.duplicates.get(
                "strategy"
            )
        ),

        "duplicate_count":
        (
            session.duplicates.get(
                "duplicate_count",
                0,
            )
        ),

        "duplicate_groups":
        (
            session.duplicates.get(
                "duplicate_groups",
                0,
            )
        ),

        # ===================================
        # EXPLAINABILITY READINESS
        # ===================================

        "can_open_explainability":
        (
            session.analysis.get(
                "analysis_complete",
                False,
            )
        ),
    }