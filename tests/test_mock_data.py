import pandas as pd

from src.data.generate_mock import generate_mock


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
