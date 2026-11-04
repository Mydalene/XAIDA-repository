# ============================================================
# XAIDA AUTOENCODER
# MLP-BASED AUTOENCODER
# ============================================================

import numpy as np

from sklearn.neural_network import (
    MLPRegressor,
)

from analytics.model_registry import (
    save_model,
)

# ============================================================
# AUTOENCODER
# ============================================================

def autoencoder_scores(
    features,
    hidden_dimension=8,
    max_iter=500,
    random_seed=42,
    persist_model=True,
    session_id=None,
):

    # ========================================================
    # TRAIN AUTOENCODER
    # ========================================================

    autoencoder = MLPRegressor(

        hidden_layer_sizes=(
            hidden_dimension,
        ),

        activation="relu",

        solver="adam",

        max_iter=max_iter,

        random_state=random_seed,
    )
    
    if hasattr(
        features,
        "toarray",
    ):

        features = (
            features.toarray()
        )

    autoencoder.fit(
        features,
        features,
    )

    # ========================================================
    # RECONSTRUCT
    # ========================================================

    reconstructed = (
        autoencoder.predict(
            features
        )
    )

    # ========================================================
    # RECONSTRUCTION ERROR
    # ========================================================

    reconstruction_error = np.mean(
        np.square(
            features
            - reconstructed
        ),
        axis=1,
    )

    # ========================================================
    # MODEL PERSISTENCE
    # ========================================================

    model_path = None

    if persist_model:

        model_path = save_model(
            autoencoder,
            "autoencoder",
            session_id=session_id,
        )

    # ========================================================
    # RETURN
    # ========================================================

    return (
        reconstruction_error,
        autoencoder,
        model_path,
    )