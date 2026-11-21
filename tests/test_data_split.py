import pandas as pd

from src.data.split import create_splits, stable_split_hash


def test_temporal_split_groups_timestamps_and_hash_is_stable(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "fraudTrain.csv").write_text("x\n1\n", encoding="utf-8")
    (raw / "fraudTest.csv").write_text("x\n2\n", encoding="utf-8")
    times = pd.date_range("2020-01-01", periods=10, freq="D").repeat(2)
    train = pd.DataFrame({"trans_num": [f"tr-{i}" for i in range(20)], "timestamp": times, "source_dataset": "fraudTrain", "is_fraud": [0, 1] * 10, "cc_num": [str(i % 3) for i in range(20)]})
    test = pd.DataFrame({"trans_num": [f"te-{i}" for i in range(4)], "timestamp": pd.date_range("2020-02-01", periods=4, freq="D"), "source_dataset": "fraudTest", "is_fraud": [0, 1, 0, 1], "cc_num": [str(i % 3) for i in range(4)]})
    processed = tmp_path / "processed.parquet"
    pd.concat([train, test]).to_parquet(processed, index=False)
    result = create_splits(processed, raw, tmp_path / "splits", project_root=tmp_path, validate_audit=False)
    train_out = pd.read_parquet(tmp_path / "splits" / "train.parquet")
    val_out = pd.read_parquet(tmp_path / "splits" / "validation.parquet")
    test_out = pd.read_parquet(tmp_path / "splits" / "test.parquet")
    assert train_out.timestamp.max() < val_out.timestamp.min() < test_out.timestamp.min()
    assert not set(train_out.trans_num) & set(val_out.trans_num)
    assert not set(train_out.trans_num) & set(test_out.trans_num)
    assert not set(val_out.trans_num) & set(test_out.trans_num)
    manifest = pd.read_parquet(tmp_path / "splits" / "split_manifest.parquet")
    assert len(manifest) == 24 and manifest.trans_num.is_unique
    assert stable_split_hash(manifest) == result["split_hash"]
