
"""Train and evaluate three baselines on synthetic mock data."""

from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src.models.preprocessing import load_feature_columns
from src.models.train import train
from src.models.predict import prediction_frame


ROOT = Path(__file__).resolve().parent

# Load mock transactions and split manifest
data = pd.read_csv(
    ROOT / "data/samples/mock_transactions.csv",
    dtype={"trans_num": str},
)
manifest = pd.read_csv(
    ROOT / "data/samples/mock_split_manifest.csv",
    dtype={"trans_num": str},
)

assert data.trans_num.is_unique
assert manifest.trans_num.is_unique

df = data.merge(
    manifest, on="trans_num",
    how="left", validate="one_to_one",
)
assert df["split"].notna().all()

train_df = df[df["split"] == "train"].copy()
val_df = df[df["split"] == "validation"].copy()

assert pd.to_datetime(train_df.timestamp).max() < pd.to_datetime(val_df.timestamp).min()

numeric, categorical = load_feature_columns()
features = numeric + categorical

X_train = train_df[features].copy()
y_train = train_df["is_fraud"].astype(int)
X_val = val_df[features].copy()
y_val = val_df["is_fraud"].astype(int)

for col in categorical:
    X_train[col] = X_train[col].astype(object).fillna("__MISSING__")
    X_val[col] = X_val[col].astype(object).fillna("__MISSING__")

results_dir = ROOT / "results/baseline/mock"
artifacts_dir = ROOT / "artifacts/mock"
results_dir.mkdir(parents=True, exist_ok=True)
artifacts_dir.mkdir(parents=True, exist_ok=True)

summary = []

for model_id in ("lr", "rf", "lgbm"):
    print(f"\nTraining: {model_id}")

    model, train_time = train(
        {"model_id": model_id, "seed": 42},
        X_train, y_train,
    )

    pred = prediction_frame(
        model, X_val,
        val_df["trans_num"].to_numpy(),
        model_id, "validation",
    )

    ap = average_precision_score(y_val, pred["score"])

    pred.to_csv(
        results_dir / f"{model_id}_predictions.csv",
        index=False,
    )

    model_path = artifacts_dir / f"{model_id}.joblib"
    joblib.dump(model, model_path)
    loaded = joblib.load(model_path)

    np.testing.assert_allclose(
        model.predict_proba(X_val),
        loaded.predict_proba(X_val),
    )

    summary.append({
        "model_id": model_id,
        "average_precision": ap,
        "train_seconds": train_time,
        "seed": 42,
        "feature_set": "baseline_v1",
        "dataset": "mock",
    })

    print(f"AP={ap:.4f}, training time={train_time:.3f}s")

pd.DataFrame(summary).to_csv(
    results_dir / "metrics.csv",
    index=False,
)

print("\nMOCK BASELINE RUN COMPLETED")
