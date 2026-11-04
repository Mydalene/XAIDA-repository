import numpy as np

from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest

from analytics.autoencoder import (
    autoencoder_scores,
)


def scale_vector(values):

    values = np.asarray(values)

    return (
        values
        - values.min()
    ) / (
        values.max()
        - values.min()
        + 1e-8
    )


def detect_anomalies(
    features,
    session_id=None,
    contamination=0.05,
    clusters=3,
    seed=42,
    isolation_weight=0.40,
    kmeans_weight=0.20,
    autoencoder_weight=0.40,
):

    total_weight = (

        isolation_weight
        + kmeans_weight
        + autoencoder_weight

    )

    if (

        isolation_weight < 0
        or kmeans_weight < 0
        or autoencoder_weight < 0

    ):

        raise ValueError(
            "Ensemble weights must be non-negative."
        )

    total_weight = (

        isolation_weight
        + kmeans_weight
        + autoencoder_weight

    )

    if total_weight <= 0:

        raise ValueError(
            "Ensemble weights cannot all be zero."
        )

    isolation_weight /= total_weight
    kmeans_weight /= total_weight
    autoencoder_weight /= total_weight

    # ========================================================
    # ISOLATION FOREST
    # ========================================================

    isolation_model = IsolationForest(
        contamination=contamination,
        random_state=seed,
    )

    isolation_model.fit(
        features
    )

    isolation_scores = (
        -isolation_model.score_samples(
            features
        )
    )

    # ========================================================
    # KMEANS
    # ========================================================

    kmeans_model = KMeans(
        n_clusters=clusters,
        random_state=seed,
        n_init=10,
    )

    labels = (
        kmeans_model.fit_predict(
            features
        )
    )

    centroids = (
        kmeans_model.cluster_centers_
    )

    kmeans_scores = (
        np.linalg.norm(
            features
            - centroids[labels],
            axis=1,
        )
    )

    # ========================================================
    # AUTOENCODER
    # ========================================================

    (
        auto_scores,
        autoencoder_model,
        autoencoder_path,
    ) = autoencoder_scores(
        features,
        session_id=session_id,
    )

    # ========================================================
    # NORMALISE
    # ========================================================

    isolation_scaled = (
        scale_vector(
            isolation_scores
        )
    )

    kmeans_scaled = (
        scale_vector(
            kmeans_scores
        )
    )

    auto_scaled = (
        scale_vector(
            auto_scores
        )
    )

    # ========================================================
    # ENSEMBLE
    # ========================================================

    ensemble_scores = (

        isolation_weight
        * isolation_scaled

        +

        kmeans_weight
        * kmeans_scaled

        +

        autoencoder_weight
        * auto_scaled
    )

    threshold = np.quantile(
        ensemble_scores,
        1 - contamination,
    )

    flags = (
        ensemble_scores
        >= threshold
    )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    anomaly_rate = (
        np.sum(flags)
        / len(flags)
    ) * 100

    if anomaly_rate < 2:

        risk_level = "Low"

    elif anomaly_rate < 5:

        risk_level = "Moderate"

    else:

        risk_level = "High"

    return (

        ensemble_scores,

        flags,

        threshold,

        isolation_scaled,

        kmeans_scaled,

        auto_scaled,

        risk_level,

        isolation_model,

        kmeans_model,

        autoencoder_model,

        autoencoder_path,

    )