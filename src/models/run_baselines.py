
"""Run LR, RF, and LightGBM baselines on Sparkov temporal splits."""

import argparse
import json
import subprocess
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import average_precision_score

from src.models.preprocessing import load_feature_columns
from src.models.train import train
from src.models.predict import prediction_frame
from src.data.split import stable_split_hash


ROOT = Path(__file__).resolve().parents[2]


def get_commit_hash():
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=ROOT / "data" / "splits",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "baseline" / "sparkov",
    )
    args = parser.parse_args()

    train_path = args.data_dir / "train.parquet"
    val_path = args.data_dir / "validation.parquet"
    manifest_path = args.data_dir / "split_manifest.parquet"
    metadata_path = args.data_dir / "split_metadata.json"

    required = [train_path, val_path, manifest_path, metadata_path]

    for path in required:
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing {path}. Ask Toan for validated Sparkov splits."
            )

    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    manifest = pd.read_parquet(manifest_path)

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )

    # Verify that the split manifest matches its metadata.
    actual_split_hash = stable_split_hash(manifest)
    expected_split_hash = metadata["split_hash"]

    if actual_split_hash != expected_split_hash:
        raise ValueError(
            "Split hash mismatch: manifest and metadata are inconsistent."
        )


    model_config = yaml.safe_load(
        (ROOT / "configs/models/baseline.yaml").read_text(
            encoding="utf-8"
        )
    )

    numeric, categorical = load_feature_columns()
    features = numeric + categorical

    required_columns = set(
        features + ["trans_num", "timestamp", "is_fraud"]
    )

    for name, frame in [
        ("train", train_df),
        ("validation", val_df),
    ]:
        missing = required_columns - set(frame.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {missing}")

        if frame["trans_num"].isna().any():
            raise ValueError(f"{name} has missing IDs")

        if frame["trans_num"].duplicated().any():
            raise ValueError(f"{name} has duplicate IDs")

        if not set(frame["is_fraud"].unique()) <= {0, 1}:
            raise ValueError(f"{name} has invalid labels")

    if not (
        train_df["timestamp"].max()
        < val_df["timestamp"].min()
    ):
        raise ValueError("Temporal split overlap detected")

    train_ids = set(train_df["trans_num"])
    val_ids = set(val_df["trans_num"])

    if train_ids & val_ids:
        raise ValueError("Train/validation ID overlap")

    expected = manifest.set_index("trans_num")["split"]

    for name, ids in [
        ("train", train_df["trans_num"]),
        ("validation", val_df["trans_num"]),
    ]:
        if not expected.reindex(ids).eq(name).all():
            raise ValueError(f"{name} manifest mismatch")

    X_train = train_df[features].copy()
    y_train = train_df["is_fraud"].astype(int)
    X_val = val_df[features].copy()
    y_val = val_df["is_fraud"].astype(int)

    for column in categorical:
        X_train[column] = (
            X_train[column].astype(object).fillna("__MISSING__")
        )
        X_val[column] = (
            X_val[column].astype(object).fillna("__MISSING__")
        )

    output_dir = args.output_dir
    artifact_dir = ROOT / "artifacts" / "models"

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    seed = model_config["experiment"]["seed"]
    commit_hash = get_commit_hash()
    split_hash = metadata["split_hash"]

    summary = []

    for model_id in ("lr", "rf", "lgbm"):
        print(f"Training {model_id} on Sparkov ...", flush=True)

        fitted_model, elapsed = train(
            {"model_id": model_id, "seed": seed},
            X_train,
            y_train,
        )

        predictions = prediction_frame(
            fitted_model,
            X_val,
            val_df["trans_num"].to_numpy(),
            model_id,
            "validation",
        )

        ap = average_precision_score(
            y_val, predictions["score"]
        )

        predictions.to_csv(
            output_dir / f"{model_id}_predictions.csv",
            index=False,
        )

        joblib.dump(
            fitted_model,
            artifact_dir / f"{model_id}.joblib",
        )

        summary.append({
            "model_id": model_id,
            "average_precision": float(ap),
            "train_seconds": float(elapsed),
            "seed": seed,
            "feature_set": "baseline_v1",
            "strategy": "none",
            "split_hash": split_hash,
            "commit_hash": commit_hash,
            "train_rows": len(train_df),
            "validation_rows": len(val_df),
        })

        print(
            f"{model_id}: AP={ap:.5f}, time={elapsed:.2f}s",
            flush=True,
        )

    pd.DataFrame(summary).to_csv(
        output_dir / "metrics.csv",
        index=False,
    )

    print("SPARKOV BASELINE RUN COMPLETED")


if __name__ == "__main__":
    run()
