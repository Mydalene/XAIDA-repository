import pandas as pd
import numpy as np
import shap

from sklearn.ensemble import IsolationForest


# ==================================================
# SHAP EXPLAINABILITY
# ==================================================

def generate_shap_explanations(
    features,
    flagged_indices,
    feature_names,
    contamination=0.05,
    seed=42,
):
    """
    Generate SHAP explanations for anomalous records.

    Parameters
    ----------
    features : ndarray
        Transformed feature matrix.

    flagged_indices : ndarray
        Row indices flagged as anomalies.

    feature_names : list
        Original feature names after preprocessing.

    contamination : float
        Isolation Forest contamination level.

    seed : int
        Random seed.

    Returns
    -------
    shap_values
        SHAP values for anomalous rows.

    top_features
        DataFrame of most influential features.

    explanations
        Human-readable explanation per anomaly.
    """

    # ------------------------------------------
    # TRAIN ISOLATION FOREST
    # ------------------------------------------

    model = IsolationForest(
        contamination=contamination,
        random_state=seed,
    )

    model.fit(features)

    # ------------------------------------------
    # ANOMALOUS RECORDS ONLY
    # ------------------------------------------

    explain_rows = features[
        flagged_indices
    ]

    # ------------------------------------------
    # SHAP EXPLAINER
    # ------------------------------------------

    explainer = shap.Explainer(
        model,
        features,
    )

    shap_values = explainer(
        explain_rows
    )

    # ------------------------------------------
    # GLOBAL FEATURE IMPORTANCE
    # ------------------------------------------

    mean_importance = np.abs(
        shap_values.values
    ).mean(axis=0)

    top_features = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": mean_importance,
        }
    )

    top_features = (
        top_features
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    # ------------------------------------------
    # RECORD-LEVEL EXPLANATIONS
    # ------------------------------------------

    explanations = []

    for row_values in shap_values.values:

        # Top 3 contributing features

        top_indices = np.argsort(
            np.abs(row_values)
        )[-3:]

        top_indices = top_indices[::-1]

        top_columns = [
            feature_names[idx]
            for idx in top_indices
        ]

        explanation = ", ".join(
            top_columns
        )

        explanations.append(
            explanation
        )

    # ------------------------------------------
    # RETURN RESULTS
    # ------------------------------------------

    return (
        shap_values,
        top_features.head(10),
        explanations,
    )