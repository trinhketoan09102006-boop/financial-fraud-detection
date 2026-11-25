
"""Tests for the fraud detection baseline models."""

import joblib
import numpy as np
import pandas as pd
import pytest

from src.models.preprocessing import (
    build_preprocessor,
    load_feature_columns,
)
from src.models.train import build_model, train
from src.models.predict import predict_score, prediction_frame


@pytest.fixture
def sample_data():
    """Create a small dataset with both labels."""
    numeric, categorical = load_feature_columns()

    rows = []
    for i in range(40):
        rows.append({
            "amt": float(i * 10 + 1),
            "hour": i % 24,
            "day_of_week": i % 7,
            "month": 1,
            "is_weekend": int(i % 7 >= 5),
            "age_at_transaction": 20 + i % 30,
            "merchant_distance_km": float(i % 100),
            "merchant": f"merchant_{i % 4}",
            "category": "grocery" if i % 2 else "travel",
        })

    X = pd.DataFrame(rows)
    y = pd.Series([i % 2 for i in range(40)])
    return X[numeric + categorical], y


@pytest.mark.parametrize("model_id", ["lr", "rf", "lgbm"])
def test_train_and_predict(model_id, sample_data):
    X, y = sample_data

    model, elapsed = train(
        {"model_id": model_id, "seed": 42},
        X,
        y,
    )

    scores = predict_score(model, X)

    assert len(scores) == len(X)
    assert np.isfinite(scores).all()
    assert ((scores >= 0) & (scores <= 1)).all()
    assert elapsed >= 0


@pytest.mark.parametrize("model_id", ["lr", "rf", "lgbm"])
def test_save_and_load_model(model_id, sample_data, tmp_path):
    X, y = sample_data
    model, _ = train({"model_id": model_id}, X, y)

    path = tmp_path / f"{model_id}.joblib"
    joblib.dump(model, path)

    loaded = joblib.load(path)

    np.testing.assert_allclose(
        predict_score(model, X),
        predict_score(loaded, X),
    )


def test_unseen_category(sample_data):
    X, y = sample_data
    model, _ = train({"model_id": "lr"}, X, y)

    X_new = X.iloc[:2].copy()
    X_new["merchant"] = "never_seen_merchant"
    X_new["category"] = "never_seen_category"

    scores = predict_score(model, X_new)
    assert len(scores) == 2
    assert np.isfinite(scores).all()


def test_prediction_ids(sample_data):
    X, y = sample_data
    model, _ = train({"model_id": "lr"}, X, y)

    ids = [f"tx-{i}" for i in range(len(X))]
    result = prediction_frame(
        model, X, ids, "lr", "validation"
    )

    assert list(result.columns) == [
        "trans_num", "model_id", "score", "split"
    ]
    assert result["trans_num"].tolist() == ids
    assert result["trans_num"].is_unique


def test_preprocessing_not_fit_before_training():
    preprocessor = build_preprocessor()
    assert not hasattr(preprocessor, "transformers_")


def test_unknown_model_raises():
    with pytest.raises(ValueError):
        build_model("invalid")

def test_validation_does_not_change_preprocessing(sample_data):
    """Validation must not influence fitted preprocessing."""
    X_train, y_train = sample_data

    model, _ = train(
        {"model_id": "lr", "seed": 42},
        X_train,
        y_train,
    )

    preprocessor = model.named_steps["preprocessor"]
    numeric_pipeline = preprocessor.named_transformers_["numeric"]
    scaler = numeric_pipeline.named_steps["scaler"]

    # Fitted statistics must come from train only.
    train_means = scaler.mean_.copy()
    train_scales = scaler.scale_.copy()

    # Create validation with extreme and unseen values.
    X_val = X_train.iloc[:5].copy()
    X_val["amt"] = 999999999.0
    X_val["merchant"] = "unseen_merchant"
    X_val["category"] = "unseen_category"

    scores = predict_score(model, X_val)

    assert len(scores) == len(X_val)
    assert np.isfinite(scores).all()

    # Predicting on validation must not refit preprocessing.
    np.testing.assert_array_equal(
        scaler.mean_,
        train_means,
    )
    np.testing.assert_array_equal(
        scaler.scale_,
        train_scales,
    )


def test_excluded_fields_not_used(sample_data):
    """ID and label must not be part of baseline features."""
    numeric, categorical = load_feature_columns()
    features = set(numeric + categorical)

    excluded = {
        "trans_num",
        "cc_num",
        "is_fraud",
        "timestamp",
        "dob",
        "unix_time",
        "source_dataset",
        "first",
        "last",
        "street",
    }

    assert features.isdisjoint(excluded)
