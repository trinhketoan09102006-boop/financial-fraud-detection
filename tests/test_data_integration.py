import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.data.audit import sha256_file
from src.data.split import stable_split_hash


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed" / "transactions.parquet"
SPLITS = ROOT / "data" / "splits"


@pytest.mark.skipif(not all((RAW / f).is_file() for f in ("fraudTrain.csv", "fraudTest.csv")), reason="Full raw dataset is not available")
@pytest.mark.skipif(not PROCESSED.is_file(), reason="Run the full pipeline before integration validation")
def test_full_pipeline_artifacts_preserve_rows_time_contract_and_hashes():
    audit = json.loads((ROOT / "docs" / "data_manifest.json").read_text(encoding="utf-8"))
    finding = next(row for row in audit["findings"] if row["check"] == "UNIX_TIME_STALE_BY_7_CALENDAR_YEARS")
    assert finding["status"] == "WARNING"
    assert not any(row["status"] == "BLOCKER" for row in audit["findings"])
    assert all(sha256_file(RAW / name) == info["sha256"] for name, info in audit["files"].items())
    for info in audit["files"].values():
        assert info["unix_matches_timestamp_plus_7y"] == info["rows"]
        assert info["unix_timestamp_decreases"] == 0

    data = pd.read_parquet(PROCESSED)
    assert len(data) == 1_852_394
    assert data["trans_num"].notna().all() and data["trans_num"].is_unique
    assert "timestamp" in data and "unix_time" not in data
    assert not {"first", "last", "street"} & set(data.columns)
    assert data["is_fraud"].isin([0, 1]).all()

    schema = yaml.safe_load((ROOT / "configs" / "data_schema.yaml").read_text(encoding="utf-8"))
    features = yaml.safe_load((ROOT / "configs" / "base_features.yaml").read_text(encoding="utf-8"))
    assert schema["canonical_time_source"] == "trans_date_trans_time"
    selected = set(features["features"]["numeric"] + features["features"]["categorical"])
    assert "unix_time" not in selected

    split_frames = {name: pd.read_parquet(SPLITS / f"{name}.parquet") for name in ("train", "validation", "test")}
    ids = {name: set(frame["trans_num"]) for name, frame in split_frames.items()}
    assert not (ids["train"] & ids["validation"] or ids["train"] & ids["test"] or ids["validation"] & ids["test"])
    assert sum(map(len, split_frames.values())) == len(data)
    assert split_frames["train"].timestamp.max() < split_frames["validation"].timestamp.min()
    assert split_frames["validation"].timestamp.max() < split_frames["test"].timestamp.min()
    manifest = pd.read_parquet(SPLITS / "split_manifest.parquet")
    assert len(manifest) == len(data) and manifest["trans_num"].is_unique
    event_splits = data[["trans_num", "timestamp"]].merge(manifest, on="trans_num", validate="one_to_one")
    assert event_splits.groupby("timestamp", observed=True)["split"].nunique().max() == 1
    metadata = json.loads((SPLITS / "split_metadata.json").read_text(encoding="utf-8"))
    assert stable_split_hash(manifest) == metadata["split_hash"]
    assert metadata["split_hash"] == "70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255"
