import json

import pandas as pd

from src.data.audit import run_audit


def _source_frame(prefix, start, n=3):
    times = pd.date_range(start, periods=n, freq="min")
    return pd.DataFrame({
        "": range(n), "trans_date_trans_time": times.astype(str), "cc_num": ["123456789012"] * n,
        "merchant": ["merchant"] * n, "category": ["food"] * n, "amt": [1.0] * n,
        "first": ["Synthetic"] * n, "last": ["Person"] * n, "gender": ["F"] * n,
        "street": ["123 Example St"] * n, "city": ["Town"] * n, "state": ["CA"] * n,
        "zip": ["00001"] * n, "lat": [37.0] * n, "long": [-122.0] * n, "city_pop": [1] * n,
        "job": ["Tester"] * n, "dob": ["1980-01-01"] * n, "trans_num": [f"{prefix}-{i}" for i in range(n)],
        "unix_time": [1] * n, "merch_lat": [37.0] * n, "merch_long": [-122.0] * n,
        "is_fraud": [0, 1, 0][:n],
    })


def test_full_audit_writes_only_aggregate_outputs(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    _source_frame("train", "2020-01-01", 3).to_csv(raw / "fraudTrain.csv", index=False)
    _source_frame("test", "2020-02-01", 3).to_csv(raw / "fraudTest.csv", index=False)
    manifest = run_audit(raw, tmp_path, chunksize=2)
    assert manifest["files"]["fraudTrain.csv"]["rows"] == 3
    assert manifest["comparison"]["strict_test_after_train"]
    assert any(item["check"] == "UNIX_TIME_UNEXPLAINED_INCONSISTENCY" and item["status"] == "BLOCKER" for item in manifest["findings"])
    output = (tmp_path / "docs" / "data_audit.md").read_text(encoding="utf-8")
    assert "Synthetic" not in output and "123 Example St" not in output
    saved = json.loads((tmp_path / "docs" / "data_manifest.json").read_text(encoding="utf-8"))
    assert "row_fingerprints" not in saved["files"]["fraudTrain.csv"]


def test_pipeline_stops_split_on_audit_blocker(monkeypatch):
    from src.data import pipeline

    monkeypatch.setattr(pipeline, "run_audit", lambda: {"findings": [{"status": "BLOCKER", "check": "unix_time_consistency"}]})
    try:
        pipeline.run("split")
    except RuntimeError as error:
        assert "BLOCKER" in str(error)
    else:
        raise AssertionError("split stage should stop when audit has a blocker")
