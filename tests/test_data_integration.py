import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
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
    normalized_arrow_schema = pq.read_schema(PROCESSED)
    assert len(data) == 1_852_394
    assert data["trans_num"].notna().all() and data["trans_num"].is_unique
    assert "timestamp" in data and "unix_time" not in data
    assert not {"first", "last", "street"} & set(data.columns)
    assert data["is_fraud"].isin([0, 1]).all()

    schema = yaml.safe_load((ROOT / "configs" / "data_schema.yaml").read_text(encoding="utf-8"))
    for name, spec in schema["fields"].items():
        if spec["type"] == "string":
            assert normalized_arrow_schema.field(name).type == pa.string(), (name, normalized_arrow_schema.field(name).type)
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
    manifest_schema = pq.read_schema(SPLITS / "split_manifest.parquet")
    assert manifest_schema.field("trans_num").type == pa.string()
    assert manifest_schema.field("split").type == pa.string()
    for name in ("train", "validation", "test"):
        split_schema = pq.read_schema(SPLITS / f"{name}.parquet")
        for field in ("trans_num", "cc_num", "merchant", "category", "gender", "city", "state", "zip", "job", "source_dataset"):
            assert split_schema.field(field).type == pa.string(), (name, field, split_schema.field(field).type)
    assert len(manifest) == len(data) and manifest["trans_num"].is_unique
    event_splits = data[["trans_num", "timestamp"]].merge(manifest, on="trans_num", validate="one_to_one")
    assert event_splits.groupby("timestamp", observed=True)["split"].nunique().max() == 1
    metadata = json.loads((SPLITS / "split_metadata.json").read_text(encoding="utf-8"))
    assert stable_split_hash(manifest) == metadata["split_hash"]
    assert metadata["split_hash"] == "aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8"
    assert metadata["cutoff_policy"] == "nearest_row_count"
    assert metadata["rows"] == {"train": 1_037_340, "validation": 259_335, "test": 555_719}
