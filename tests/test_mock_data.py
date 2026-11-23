import pandas as pd
import pyarrow as pa
import yaml
from pathlib import Path

from src.data.generate_mock import generate_mock


ROOT = Path(__file__).resolve().parents[1]


def test_mock_data_is_synthetic_temporal_and_covers_each_split(tmp_path):
    data, manifest = generate_mock(tmp_path, rows_per_split=100, seed=7)
    assert len(data) == 300
    assert data.trans_num.is_unique
    assert set(manifest.columns) == {"trans_num", "split"}
    assert set(manifest.split) == {"train", "validation", "test"}
    labels = data.merge(manifest, on="trans_num").groupby("split").is_fraud.agg(["min", "max"])
    assert (labels["min"] == 0).all() and (labels["max"] == 1).all()
    times = data.groupby(manifest.set_index("trans_num").loc[data.trans_num, "split"]).timestamp
    ranges = data.assign(split=manifest.set_index("trans_num").loc[data.trans_num, "split"].to_numpy()).groupby("split").timestamp.agg(["min", "max"])
    assert ranges.loc["train", "max"] < ranges.loc["validation", "min"] < ranges.loc["test", "min"]
    assert ((ranges["max"] - ranges["min"]).dt.days >= 7).all()
    assert data.timestamp.duplicated().any()
    loaded = pd.read_csv(tmp_path / "mock_transactions.csv")
    assert loaded.trans_num.is_unique
    assert "merchant_new" in set(loaded.merchant)
    assert "unix_time" not in data
    assert set(data.source_dataset) <= {"fraudTrain", "fraudTest"}
    assert str(data.trans_num.dtype) == "string"
    assert str(data.cc_num.dtype) == "string"
    assert data.timestamp.dtype == "datetime64[ns]"
    assert data.dob.dtype == "datetime64[ns]"
    assert str(pa.Table.from_pandas(data, preserve_index=False).schema.field("timestamp").type) == "timestamp[ns]"

    schema = yaml.safe_load((ROOT / "configs" / "data_schema.yaml").read_text(encoding="utf-8"))
    assert set(data.columns) == set(schema["fields"])
    arrow_schema = pa.Table.from_pandas(data, preserve_index=False).schema
    type_map = {
        "string": "string",
        "datetime64[ns]": "timestamp[ns]",
        "float64": "double",
        "float32": "float",
        "int64": "int64",
        "int8": "int8",
    }
    for name, field in schema["fields"].items():
        expected = type_map[field["type"]]
        assert str(arrow_schema.field(name).type) == expected, (name, expected, arrow_schema.field(name).type)


def test_checked_in_mock_csv_matches_normalized_contract():
    schema = yaml.safe_load((ROOT / "configs" / "data_schema.yaml").read_text(encoding="utf-8"))
    data = pd.read_csv(
        ROOT / "data" / "samples" / "mock_transactions.csv",
        dtype={"trans_num": "string", "cc_num": "string", "source_dataset": "string"},
        parse_dates=["timestamp", "dob"],
    )
    manifest = pd.read_csv(ROOT / "data" / "samples" / "mock_split_manifest.csv", dtype={"trans_num": "string"})
    assert set(data.columns) == set(schema["fields"])
    assert "unix_time" not in data
    assert data["trans_num"].is_unique and data["trans_num"].notna().all()
    assert data["trans_num"].str.startswith("mock-").all()
    assert set(data["source_dataset"]) <= {"fraudTrain", "fraudTest"}
    assert manifest["trans_num"].is_unique and len(manifest) == len(data)
    assert set(manifest["trans_num"]) == set(data["trans_num"])
