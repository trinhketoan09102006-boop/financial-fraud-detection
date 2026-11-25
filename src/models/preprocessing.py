
"""Shared preprocessing for fraud detection baselines."""

from pathlib import Path

import yaml
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
FEATURE_CONFIG = ROOT / "configs" / "base_features.yaml"


def load_feature_columns():
    """Load features from the team's YAML configuration."""
    with FEATURE_CONFIG.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    numeric = list(config["features"]["numeric"])
    categorical = list(config["features"]["categorical"])

    if set(numeric) & set(categorical):
        raise ValueError("Numeric and categorical columns overlap.")

    if set(numeric + categorical) & set(config["excluded_fields"]):
        raise ValueError("Excluded fields found in model features.")

    return numeric, categorical


def build_preprocessor():
    """Create an unfitted preprocessing transformer."""
    numeric, categorical = load_feature_columns()

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="constant",
                fill_value="__MISSING__",
            ),
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=True,
            ),
        ),
    ])

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric),
            ("categorical", categorical_pipeline, categorical),
        ],
        sparse_threshold=1.0,
    )
