
"""Training module for fraud detection baselines."""

import time
from pathlib import Path

import yaml
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .preprocessing import build_preprocessor


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs" / "models" / "baseline.yaml"

MODEL_CLASSES = {
    "lr": LogisticRegression,
    "rf": RandomForestClassifier,
    "lgbm": LGBMClassifier,
}


def load_model_config(path=DEFAULT_CONFIG):
    """Load and validate baseline YAML configuration."""
    with Path(path).open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict) or "models" not in config:
        raise ValueError("Invalid baseline model configuration.")

    return config


def build_model(model_id, seed=42, config_path=DEFAULT_CONFIG):
    """Create a classifier using YAML hyperparameters."""
    if model_id not in MODEL_CLASSES:
        raise ValueError(f"Unknown model: {model_id}")

    config = load_model_config(config_path)

    if model_id not in config["models"]:
        raise ValueError(f"Missing model config: {model_id}")

    params = dict(config["models"][model_id])
    params["random_state"] = seed

    return MODEL_CLASSES[model_id](**params)


def train(config, X_train, y_train):
    """Fit preprocessing and classifier using train only."""
    model_id = config["model_id"]
    seed = config.get("seed", 42)
    config_path = config.get("config_path", DEFAULT_CONFIG)

    pipeline = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", build_model(model_id, seed, config_path)),
    ])

    started = time.perf_counter()
    pipeline.fit(X_train, y_train)
    elapsed = time.perf_counter() - started

    return pipeline, elapsed
