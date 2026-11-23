import pandas as pd

from src.data.split import choose_timestamp_cutoff, create_splits, stable_split_hash


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


def test_nearest_row_count_cutoff_does_not_drop_the_boundary_group(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "fraudTrain.csv").write_text("x\n1\n", encoding="utf-8")
    (raw / "fraudTest.csv").write_text("x\n2\n", encoding="utf-8")
    timestamps = pd.date_range("2020-01-01", periods=10, freq="D").repeat(2)
    source_train = pd.DataFrame({
        "trans_num": [f"tr-{i}" for i in range(20)], "timestamp": timestamps,
        "source_dataset": "fraudTrain", "is_fraud": [0, 1] * 10,
        "cc_num": [str(i % 3) for i in range(20)],
    })
    test = pd.DataFrame({
        "trans_num": [f"te-{i}" for i in range(4)],
        "timestamp": pd.date_range("2020-02-01", periods=4, freq="D"),
        "source_dataset": "fraudTest", "is_fraud": [0, 1, 0, 1],
        "cc_num": [str(i % 3) for i in range(4)],
    })
    processed = tmp_path / "processed.parquet"
    pd.concat([source_train, test]).to_parquet(processed, index=False)

    groups = source_train.groupby("timestamp", sort=True).size()
    proposed_cutoff = choose_timestamp_cutoff(groups, target_train_rows=16, policy="nearest_row_count")
    assert (source_train.timestamp < proposed_cutoff).sum() == 16
    assert proposed_cutoff == pd.Timestamp("2020-01-09")

    result = create_splits(
        processed, raw, tmp_path / "proposed-splits", project_root=tmp_path / "proposed-project",
        validate_audit=False, cutoff_policy="nearest_row_count",
    )
    train = pd.read_parquet(tmp_path / "proposed-splits" / "train.parquet")
    validation = pd.read_parquet(tmp_path / "proposed-splits" / "validation.parquet")
    test_out = pd.read_parquet(tmp_path / "proposed-splits" / "test.parquet")
    assert len(train) == 16
    assert train.timestamp.max() < validation.timestamp.min() < test_out.timestamp.min()
    assert not (set(train.trans_num) & set(validation.trans_num))
    assert not (set(train.trans_num) & set(test_out.trans_num))
    assert not (set(validation.trans_num) & set(test_out.trans_num))
    manifest = pd.read_parquet(tmp_path / "proposed-splits" / "split_manifest.parquet")
    assert manifest.trans_num.is_unique and len(manifest) == 24
    assert result["cutoff_policy"] == "nearest_row_count"


def test_legacy_cutoff_remains_available_for_approved_baseline():
    timestamps = pd.date_range("2020-01-01", periods=10, freq="D")
    groups = pd.Series([2] * 10, index=timestamps)
    cutoff = choose_timestamp_cutoff(groups, target_train_rows=16, policy="legacy")
    assert cutoff == pd.Timestamp("2020-01-08")
    assert int(groups.loc[groups.index < cutoff].sum()) == 14
