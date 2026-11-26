import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml
from pathlib import Path

from src.data.arrow_schema import dataframe_to_arrow_table, load_contract_arrow_schema
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

    schema = yaml.safe_load((ROOT / "configs" / "data_schema.yaml").read_text(encoding="utf-8"))
    assert set(data.columns) == set(schema["fields"])
    # Validate the contract serialization boundary. Direct pandas inference can
    # choose large_string on newer pandas/pyarrow even when the writer contract
    # explicitly requires Arrow string.
    parquet_path = tmp_path / "mock_transactions.parquet"
    table = dataframe_to_arrow_table(data, strict=True)
    pq.write_table(table, parquet_path)
    arrow_schema = pq.read_schema(parquet_path)
    contract_schema = load_contract_arrow_schema()
    assert arrow_schema.equals(contract_schema, check_metadata=False)
    assert arrow_schema.field("timestamp").type.tz is None
    round_trip = pq.read_table(parquet_path)
    assert round_trip.equals(table, check_metadata=False)


@pytest.mark.parametrize("backend", ["object", "pandas_string", "large_string"])
def test_mock_contract_conversion_accepts_string_backends(tmp_path, backend):
    data, _ = generate_mock(tmp_path, rows_per_split=10, seed=31)
    contract_schema = load_contract_arrow_schema()
    text_fields = [field.name for field in contract_schema if pa.types.is_string(field.type)]
    expected_values = {name: data[name].tolist() for name in text_fields}
    for name in text_fields:
        if backend == "object":
            data[name] = data[name].astype(object)
        elif backend == "pandas_string":
            data[name] = data[name].astype("string")
        else:
            large = pa.array(data[name], type=pa.large_string())
            data[name] = pd.Series(large, index=data.index, dtype=pd.ArrowDtype(pa.large_string()))

    inferred = pa.Table.from_pandas(data, preserve_index=False)
    if backend == "large_string":
        assert inferred.schema.field("trans_num").type == pa.large_string()
    contract_table = dataframe_to_arrow_table(data, strict=True)
    assert contract_table.schema.equals(contract_schema, check_metadata=False)
    for name in text_fields:
        expected = [None if pd.isna(value) else str(value) for value in expected_values[name]]
        assert contract_table.column(name).to_pylist() == expected, name

    output = tmp_path / f"mock_{backend}.parquet"
    pq.write_table(contract_table, output)
    assert pq.read_schema(output).equals(contract_schema, check_metadata=False)
    assert pq.read_table(output).equals(contract_table, check_metadata=False)


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
