# ============================================================
# XAIDA 4.0
# analytics/analysis_engine.py
# ============================================================

import numpy as np
import hashlib
import pandas as pd

from analytics.model_registry import (
    save_model,
)

from analytics.persistence import (
    save_analysis_artifact,
)

from analytics.preprocessing import (
    transform_features,
)

from analytics.anomaly_detection import (
    detect_anomalies,
)

from analytics.explainability import (
    generate_shap_explanations,
)

from audit.audit_logger import (
    log_audit_event,
)

from dataset.version_manager import(
    create_dataset_version,
)

# ============================================================
# RUN ANALYSIS
# ============================================================

def run_analysis(
    session,
):

    # ========================================================
    # DATASET
    # ========================================================

    dataframe = (
        session.analysis.get(
            "analysis_dataset"
        )
    )

    if dataframe is None:

        dataframe = (
            session.dataset.get(
                "dataframe"
            )
        )

    if not isinstance(
        dataframe,
        pd.DataFrame,
    ):

        raise TypeError(
            f"Expected DataFrame, got {type(dataframe)}"
        )

    # ========================================================
    # FEATURE ENGINEERING
    # ========================================================

    (
        features,
        feature_names,
    ) = transform_features(
        dataframe
    )

    log_audit_event(

        session,

        stage="Feature Engineering",

        action="Features Generated",

        details=(
            f"{features.shape[1]} "
            "features created"
        ),
    )

    feature_diagnostics = {

        "feature_count":
            int(features.shape[1]),

        "record_count":
            int(features.shape[0]),

        "nan_count":
            int(
                np.isnan(features).sum()
            ),

        "inf_count":
            int(
                np.isinf(features).sum()
            ),
    }

    session.analysis[
        "feature_diagnostics"
    ] = feature_diagnostics

    log_audit_event(

        session,

        stage="Feature Engineering",

        action="Feature Validation",

        details=(

            f"NaN="
            f"{feature_diagnostics['nan_count']} "

            f"Inf="
            f"{feature_diagnostics['inf_count']}"
        ),
    )

    # ========================================================
    # ENSEMBLE ANOMALY DETECTION
    # ========================================================

    (
        scores,
        flags,
        threshold,

        isolation_scores,
        kmeans_scores,
        autoencoder_scores,

        risk_level,

        isolation_model,
        kmeans_model,
        autoencoder_model,

        autoencoder_path,

    ) = detect_anomalies(
        features,
        session_id=session.metadata["session_id"],
    )

    log_audit_event(

        session,

        stage="Analysis",

        action="Ensemble Detection",

        details=(
            f"{int(flags.sum())} "
            "anomalies detected"
        ),
    )

    isolation_model_path = (
        save_model(
            isolation_model,
            "isolation_forest",
            session_id=session.metadata["session_id"],
        )
    )

    kmeans_model_path = (
        save_model(
            kmeans_model,
            "kmeans",
            session_id=session.metadata["session_id"],
        )
    )

    # ========================================================
    # FLAGGED TRANSACTIONS
    # ========================================================

    flagged_indices = (
        dataframe.index[
            flags
        ]
    )

    flagged_positions = (
        np.where(flags)[0]
    )

    flagged_transactions = (
        dataframe.loc[
            flagged_indices
        ].copy()
    )

    flagged_transactions[
        "Risk Score"
    ] = scores[
        flags
    ]

    flagged_transactions[
        "Isolation Score"
    ] = isolation_scores[
        flags
    ]

    flagged_transactions[
        "KMeans Score"
    ] = kmeans_scores[
        flags
    ]

    flagged_transactions[
        "Autoencoder Score"
    ] = autoencoder_scores[
        flags
    ]

    # ========================================================
    # HIGH RISK TRANSACTIONS
    # ========================================================

    high_risk_transactions = (

        flagged_transactions[

            flagged_transactions[
                "Risk Score"
            ]

            >= threshold

        ]
    )

    # ========================================================
    # ANALYSIS DATAFRAME
    # ========================================================

    analysis_df = (
        dataframe.copy()
    )

    analysis_df[
        "Risk Score"
    ] = scores

    analysis_df[
        "Anomaly Flag"
    ] = flags

    analysis_df = (
        analysis_df.sort_values(
            by=[
                "Anomaly Flag",
                "Risk Score",
            ],
            ascending=[
                False,
                False,
            ],
        )
    )

    current_version = (
        create_dataset_version(
            session=session,
            dataframe=analysis_df,
            stage="Analysis",
            action="Anomaly Dataset Generated",
            metadata={
                "dataset_type": "anomaly",
            },
        )
    )

    log_audit_event(

        session,

        stage="Analysis",

        action="Analysis Dataset Generated",

        details=(
            "Anomaly attributes added"
        ),

    )
    # ========================================================
    # RISK SUMMARY
    # ========================================================

    risk_summary = {

        "risk_level":
            risk_level,

        "total_transactions":
            len(dataframe),

        "flagged_transactions":
            len(flagged_transactions),

        "high_risk_transactions":
            len(high_risk_transactions),
    }

    log_audit_event(

        session,

        stage="Analysis",

        action="Risk Assessment",

        details=(
            f"Risk Level = "
            f"{risk_level}"
        ),
    )
    
    # ========================================================
    # EXPLAINABILITY
    # ========================================================

    try:

        (
            shap_values,
            top_features,
            explanations,
        ) = generate_shap_explanations(

            features,

            flagged_positions,

            feature_names,

        )

        log_audit_event(

            session,

            stage="Explainability",

            action="Shap Explanation Generated",

            details=(
                f"{len(explanations)} "
                "explanations added"
            ),

        )

        create_explainability_dataset(
            session,
            analysis_df,
            explanations,
        )
        explanation_by_record = {
            record_index: explanation
            for record_index, explanation in zip(
                flagged_indices,
                explanations,
            )
        }
        shap_contribution_details = []
        if shap_values is not None:
            for record_index, values in zip(
                flagged_indices,
                shap_values.values,
            ):
                top_indices = np.argsort(np.abs(values))[-3:][::-1]
                shap_contribution_details.append(
                    {
                        "source_record": record_index,
                        "drivers": [
                            {
                                "feature": str(feature_names[index]),
                                "shap_value": float(values[index]),
                                "absolute_contribution": float(
                                    abs(values[index])
                                ),
                            }
                            for index in top_indices
                        ],
                    }
                )

    except Exception:

        shap_values = None

        top_features = None

        explanations = []
        explanation_by_record = {}
        shap_contribution_details = []

    # ========================================================
    # DATASET HASH
    # ========================================================

    dataset_hash = hashlib.sha256(

        dataframe.to_csv(
            index=False
        ).encode()

    ).hexdigest()

    # ========================================================
    # ANALYSIS METADATA
    # ========================================================

    analysis_metadata = {

        "model":
            "XAIDA Ensemble",

        "model_version":
            "1.0",

        "random_seed":
            42,

        "feature_count":
            int(
                features.shape[1]
            ),

        "dataset_version":
            current_version,
            
        "dataset_hash":
            dataset_hash,

        "threshold":
            float(
                threshold
            ),

        "flagged_transactions":
            int(
                len(flagged_transactions)
            ),

        "isolation_model":
            isolation_model_path,

        "kmeans_model":
            kmeans_model_path,

        "autoencoder_model":
            autoencoder_path,

        "weights": {

            "isolation_forest":
                0.40,

            "kmeans":
                0.20,

            "autoencoder":
                0.40,
        },
    }
    # ========================================================
    # RESULT OBJECT
    # ========================================================

    analysis_result = {

        "analysis_dataframe":
            analysis_df,

        "risk_level":
            risk_level,

        "risk_summary":
            risk_summary,

        "threshold":
            threshold,

        "scores":
            scores,

        "flags":
            flags,

        "flagged_transactions":
            flagged_transactions,

        "high_risk_transactions":
            high_risk_transactions,

        "isolation_scores":
            isolation_scores,

        "kmeans_scores":
            kmeans_scores,

        "autoencoder_scores":
            autoencoder_scores,

        "top_features":
            top_features,

        "explanations":
            explanations,

        "explanation_by_record":
            explanation_by_record,

        "shap_contribution_details":
            shap_contribution_details,

        "shap_values":
            shap_values,

        "feature_names":
            feature_names,

        "analysis_metadata":
            analysis_metadata,

        "model_paths": {

            "isolation_forest":
                isolation_model_path,

            "kmeans":
                kmeans_model_path,

            "autoencoder":
                autoencoder_path,
        },

    }


    
    # ========================================================
    # PERSISTENCE
    # ========================================================

    artifact_info = (

        save_analysis_artifact(
            analysis_result,
            current_version,
            session_id=session.metadata["session_id"],
        )

    )

    analysis_result[
        "artifact_info"
    ] = artifact_info

# ========================================================
# VERSIONING
# ========================================================

    session.analysis[
        "analysis_version"
    ] = current_version

    session.analysis[
        "feature_names"
    ] = feature_names

    session.analysis[
        "analysis_metadata"
    ] = analysis_metadata

    # ========================================================
    # AUDIT LOGS
    # ========================================================
        
    log_audit_event(

        session,

        stage="Analysis", 

        action="Analysis Completed",

        details=(
            f"{len(flagged_transactions)} "
            "transactions flagged"
        ),
    )

    return analysis_result

# ========================================================
# EXPLAINABILITY DATASET
# ========================================================

def create_explainability_dataset(
    session,
    analysis_df,
    explanations,
):

    explainability_df = (
        analysis_df.copy()
    )

    explainability_df[
        "Explainability Narrative"
    ] = ""

    flagged_rows = (
        explainability_df[
            explainability_df[
                "Anomaly Flag"
            ] == 1
        ].index
    )

    for idx, explanation in zip(
        flagged_rows,
        explanations,
    ):

        explainability_df.loc[
            idx,
            "Explainability Narrative"
        ] = explanation

    version = create_dataset_version(
        session=session,
        dataframe=explainability_df,
        stage="Explainability",
        action="Explainability Dataset Generated",
        metadata={
            "dataset_type": "explainability",
            "explanations_added":
                len(explanations),
        },
    )

    log_audit_event(
        session,
        stage="Explainability",
        action="Explainability Dataset Generated",
        details=(
            f"{len(explanations)} "
            "explanations enriched"
        ),
    )

    session.analysis[
        "explainability_version"
    ] = version

    session.analysis[
        "explainability_version_created"
    ] = True

    return version