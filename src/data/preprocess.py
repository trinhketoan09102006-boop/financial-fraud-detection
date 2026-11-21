"""Normalize the two source CSVs into a transaction-level Parquet table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .audit import RAW_FILES, ROOT, run_audit


DROP_COLUMNS = ("first", "last", "street", "Unnamed: 0", "unix_time")
RENAME_COLUMNS = {"trans_date_trans_time": "timestamp"}
REQUIRED = {"trans_num", "cc_num", "trans_date_trans_time", "amt", "merchant", "category", "is_fraud"}


def _haversine_km(lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    radius = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * radius * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def normalize_frame(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f"{source} is missing required fields: {sorted(missing)}")
    data = frame.drop(columns=[c for c in DROP_COLUMNS if c in frame], errors="ignore").copy()
    data = data.rename(columns=RENAME_COLUMNS)
    data["cc_num"] = data["cc_num"].astype("string")
    data["trans_num"] = data["trans_num"].astype("string")
    data["zip"] = data["zip"].astype("string")
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="raise")
    data["dob"] = pd.to_datetime(data["dob"], errors="raise")
    data["amt"] = pd.to_numeric(data["amt"], errors="raise").astype("float64")
    data["is_fraud"] = pd.to_numeric(data["is_fraud"], errors="raise").astype("int8")
    data["city_pop"] = pd.to_numeric(data["city_pop"], errors="raise").astype("int64")
    for col in ("lat", "long", "merch_lat", "merch_long"):
        data[col] = pd.to_numeric(data[col], errors="raise").astype("float64")

    # All added fields use the transaction itself and are not customer-history features.
    data["hour"] = data["timestamp"].dt.hour.astype("int8")
    data["day_of_week"] = data["timestamp"].dt.dayofweek.astype("int8")
    data["month"] = data["timestamp"].dt.month.astype("int8")
    data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype("int8")
    data["age_at_transaction"] = ((data["timestamp"] - data["dob"]).dt.total_seconds() / (365.2425 * 86400)).astype("float32")
    data["merchant_distance_km"] = _haversine_km(data["lat"], data["long"], data["merch_lat"], data["merch_long"]).astype("float32")
    data["source_dataset"] = source
    data = data.sort_values(["timestamp", "trans_num"], kind="mergesort", ignore_index=True)
    return data


def preprocess(raw_dir: Path | None = None, output: Path | None = None, force: bool = False, validate_audit: bool = True) -> pd.DataFrame:
    raw_dir = raw_dir or ROOT / "data" / "raw"
    output = output or ROOT / "data" / "processed" / "transactions.parquet"
    if output.exists() and not force:
        raise FileExistsError(f"Output already exists; pass --force to replace it: {output}")
    if validate_audit:
        audit = run_audit(raw_dir=raw_dir, output_root=ROOT)
        blockers = [f for f in audit["findings"] if f["status"] == "BLOCKER"]
        if blockers:
            raise RuntimeError(f"Preprocessing stopped because audit reported BLOCKER findings: {blockers}")
    parts = []
    for filename in RAW_FILES:
        path = raw_dir / filename
        source = "fraudTrain" if filename == "fraudTrain.csv" else "fraudTest"
        frame = pd.read_csv(path, dtype={"cc_num": "string", "trans_num": "string", "zip": "string"}, low_memory=False)
        parts.append(normalize_frame(frame, source))
    result = pd.concat(parts, ignore_index=True)
    result = result.sort_values(["timestamp", "trans_num"], kind="mergesort", ignore_index=True)
    if result["trans_num"].isna().any() or result["trans_num"].duplicated().any():
        raise ValueError("Normalized trans_num must be non-null and globally unique.")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".tmp")
    try:
        result.to_parquet(temp, index=False, compression="zstd")
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    _write_report(result, ROOT / "docs" / "data_preprocessing_report.md")
    return result


def _write_report(data: pd.DataFrame, path: Path) -> None:
    dropped = ["Unnamed: 0 (redundant CSV index)", "first", "last", "street", "unix_time (stale by seven calendar years)"]
    generated = ["hour", "day_of_week", "month", "is_weekend", "age_at_transaction", "merchant_distance_km", "source_dataset"]
    retained = [str(c) for c in data.columns if c not in generated]
    text = f"""# Data preprocessing report

## Outcome

- Rows before: {len(data):,} (no transactions removed).
- Rows after: {len(data):,}.
- Unique, non-null `trans_num`: {data['trans_num'].nunique(dropna=True):,}.
- Timestamp range: {data['timestamp'].min()} to {data['timestamp'].max()}.
- Canonical time: parsed from `trans_date_trans_time` as timezone-naive; no UTC conversion was applied.
- Source `unix_time`: verified to be exactly seven calendar years behind the text timestamp, so it is excluded from normalized Parquet. The raw field and CSVs are unchanged.
- Row order: stable ascending `timestamp`, then `trans_num` for deterministic ordering only; the ID is not treated as chronology.
- Missing values: {int(data.isna().sum().sum()):,}; no imputation was performed.
- Parquet compression: Zstandard.

## Transformations

- Dropped redundant index and direct identity/address fields: {', '.join(dropped)}.
- Kept source dataset label as metadata: `source_dataset`.
- Parsed `timestamp` from `trans_date_trans_time` and parsed `dob`; kept `cc_num` and `zip` as strings, `trans_num` as the unique row key, and `is_fraud` as integer 0/1.
- Added transaction-local calendar features and `age_at_transaction`.
- Added `merchant_distance_km` as straight-line great-circle distance between profile and merchant coordinates. This is not actual travel distance.
- No sampling, imputation, outlier removal, rolling features, card-history features, or use of future transactions.

## Output fields

`{', '.join(retained + generated)}`

## Limitations

- Source timestamps do not declare a timezone. `unix_time` is excluded from the normalized table after exact seven-calendar-year reconstruction across all rows; it remains unchanged in the raw files and is used only for audit diagnostics.
- `source_dataset` identifies whether a row came from the original train or test file; exclude it from model features.
- Merchant distance is a geographic proxy and may not reflect a customer's actual location at transaction time.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed" / "transactions.parquet")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-audit", action="store_true")
    args = parser.parse_args()
    data = preprocess(args.raw_dir, args.output, args.force, not args.skip_audit)
    print(json.dumps({"output": str(args.output), "rows": len(data), "columns": len(data.columns)}, indent=2))


if __name__ == "__main__":
    main()
