import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.data.preprocess import ARROW_STRING_COLUMNS, _to_contract_arrow_table, normalize_frame


def test_normalize_frame_preserves_ids_and_target_and_removes_direct_identity():
    raw = pd.DataFrame({
        "Unnamed: 0": [0], "trans_date_trans_time": ["2020-01-01 01:02:03"],
        "cc_num": ["001234567890"], "trans_num": ["fake-id"], "zip": ["00123"],
        "amt": [12.5], "merchant": ["m"], "category": ["c"], "gender": ["F"],
        "city": ["x"], "state": ["CA"], "lat": [37.0], "long": [-122.0],
        "city_pop": [10], "dob": ["1980-01-01"], "job": ["job"], "unix_time": [1],
        "merch_lat": [37.1], "merch_long": [-122.1], "is_fraud": [1],
        "first": ["Fake"], "last": ["Person"], "street": ["Nowhere"],
    })
    normalized = normalize_frame(raw, "fraudTrain")
    assert normalized.loc[0, "cc_num"] == "001234567890"
    assert normalized.loc[0, "zip"] == "00123"
    assert normalized.loc[0, "is_fraud"] == 1
    assert normalized.loc[0, "timestamp"] == pd.Timestamp("2020-01-01 01:02:03")
    assert not {"first", "last", "street", "Unnamed: 0"} & set(normalized.columns)
    assert "unix_time" not in normalized.columns
    assert normalized.loc[0, "merchant_distance_km"] > 0
    assert normalized.timestamp.dtype == "datetime64[ns]"
    assert normalized.dob.dtype == "datetime64[ns]"
    assert str(normalized.cc_num.dtype) == "string"
    assert str(normalized.trans_num.dtype) == "string"


def test_normalized_timestamp_parquet_precision_is_nanoseconds(tmp_path):
    raw = pd.DataFrame({
        "trans_num": ["fake-id"], "cc_num": ["123456789012"],
        "trans_date_trans_time": ["2020-01-01 01:02:03"], "dob": ["1980-01-01"],
        "amt": [12.5], "merchant": ["m"], "category": ["c"], "is_fraud": [0],
        "gender": ["F"], "city": ["x"], "state": ["CA"], "zip": ["00123"],
        "lat": [37.0], "long": [-122.0], "city_pop": [10], "job": ["job"],
        "merch_lat": [37.1], "merch_long": [-122.1],
    })
    normalized = normalize_frame(raw, "fraudTrain")
    output = tmp_path / "normalized.parquet"
    normalized.to_parquet(output, index=False)
    schema = pq.read_schema(output)
    assert str(schema.field("timestamp").type) == "timestamp[ns]"
    assert schema.field("timestamp").type.tz is None
    assert str(schema.field("dob").type) == "timestamp[ns]"


def test_normalized_parquet_uses_contract_arrow_string_even_from_large_string_backend(tmp_path):
    raw = pd.DataFrame({
        "trans_num": ["fake-id"], "cc_num": ["001234567890"],
        "trans_date_trans_time": ["2020-01-01 01:02:03"], "dob": ["1980-01-01"],
        "amt": [12.5], "merchant": ["merchant"], "category": ["category"], "is_fraud": [0],
        "gender": ["F"], "city": ["city"], "state": ["CA"], "zip": ["00123"],
        "lat": [37.0], "long": [-122.0], "city_pop": [10], "job": ["job"],
        "merch_lat": [37.1], "merch_long": [-122.1],
    })
    normalized = normalize_frame(raw, "fraudTrain")
    # Exercise the wider Arrow text type regardless of how this environment's
    # pandas string dtype is currently mapped by PyArrow.
    arrow = pa.Table.from_pandas(normalized, preserve_index=False)
    for name in ARROW_STRING_COLUMNS:
        index = arrow.schema.get_field_index(name)
        arrow = arrow.set_column(index, name, arrow.column(index).cast(pa.large_string()))
    wide_string_frame = arrow.to_pandas()

    output = tmp_path / "normalized.parquet"
    pq.write_table(_to_contract_arrow_table(wide_string_frame), output)
    schema = pq.read_schema(output)
    for name in ARROW_STRING_COLUMNS:
        assert schema.field(name).type == pa.string(), (name, schema.field(name).type)


def test_canonical_timestamp_is_parsed_from_trans_date_and_not_shifted():
    raw = pd.DataFrame({
        "trans_num": ["fake-id"], "cc_num": ["123456789012"], "trans_date_trans_time": ["2019-01-01 00:00:18"],
        "unix_time": [1325376018], "amt": [12.5], "merchant": ["m"], "category": ["c"], "is_fraud": [0],
        "gender": ["F"], "city": ["x"], "state": ["CA"], "zip": ["00123"], "lat": [37.0], "long": [-122.0],
        "city_pop": [10], "dob": ["1980-01-01"], "job": ["job"], "merch_lat": [37.1], "merch_long": [-122.1],
    })
    normalized = normalize_frame(raw, "fraudTrain")
    assert normalized.loc[0, "timestamp"] == pd.Timestamp("2019-01-01 00:00:18")
    assert normalized.loc[0, "timestamp"] != pd.to_datetime(1325376018, unit="s")
    assert "unix_time" not in normalized
