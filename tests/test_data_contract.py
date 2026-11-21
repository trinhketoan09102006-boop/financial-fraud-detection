from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_contract_required_fields_and_model_exclusions():
    schema = yaml.safe_load((ROOT / "configs" / "data_schema.yaml").read_text(encoding="utf-8"))
    features = yaml.safe_load((ROOT / "configs" / "base_features.yaml").read_text(encoding="utf-8"))
    assert set(schema["required_fields"]) <= set(schema["fields"])
    selected = set(features["features"]["numeric"] + features["features"]["categorical"])
    forbidden = {name for name, spec in schema["fields"].items() if spec.get("model_feature") is False}
    assert not selected & forbidden
    assert {"trans_num", "cc_num", "is_fraud", "source_dataset"} <= set(features["excluded_fields"])
    assert "unix_time" in features["excluded_fields"]
    assert schema["canonical_time_source"] == "trans_date_trans_time"
    assert "unix_time" not in schema["fields"]
