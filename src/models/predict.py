
"""Prediction utilities for fraud detection baselines."""

import numpy as np
import pandas as pd


def predict_score(model, X):
    """Return fraud probabilities for each transaction."""
    probabilities = model.predict_proba(X)

    # Locate the fraud class explicitly.
    classes = model.classes_
    fraud_index = list(classes).index(1)

    scores = np.asarray(
        probabilities[:, fraud_index],
        dtype=float,
    )

    if not np.isfinite(scores).all():
        raise ValueError("Non-finite prediction scores.")

    if ((scores < 0) | (scores > 1)).any():
        raise ValueError("Scores must be between 0 and 1.")

    return scores


def prediction_frame(model, X, transaction_ids, model_id, split):
    """Create prediction records using original transaction IDs."""
    scores = predict_score(model, X)
    ids = pd.Series(transaction_ids, dtype="string")

    if len(ids) != len(scores):
        raise ValueError("Transaction ID count mismatch.")

    if ids.isna().any() or ids.duplicated().any():
        raise ValueError("Invalid transaction IDs.")

    return pd.DataFrame({
        "trans_num": ids.to_numpy(),
        "model_id": model_id,
        "score": scores,
        "split": split,
    })
