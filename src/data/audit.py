"""Full-file, privacy-conscious audit for the Sparkov transaction CSVs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_FILES = ("fraudTrain.csv", "fraudTest.csv")
EXPECTED_ROWS = {"fraudTrain.csv": 1_296_675, "fraudTest.csv": 555_719}
TARGET = "is_fraud"
TIMESTAMP = "trans_date_trans_time"
ID = "trans_num"
CARD = "cc_num"
DROP_FIELDS = {"first", "last", "street"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _datetime_epoch_seconds(values: pd.Series) -> pd.Series:
    """Return Unix seconds independently of the datetime64 storage resolution."""
    ns_values = values.dt.as_unit("ns").astype("int64")
    return ns_values // 1_000_000_000


def _new_stats() -> dict[str, Any]:
    return {
        "rows": 0,
        "columns": [],
        "dtypes": {},
        "missing": Counter(),
        "blank_strings": Counter(),
        "labels": Counter(),
        "categorical_values": {},
        "card_ids": set(),
        "fraud_card_ids": set(),
        "transaction_ids": set(),
        "row_fingerprints": set(),
        "duplicate_rows": 0,
        "duplicate_transaction_ids": 0,
        "invalid_transaction_ids": 0,
        "invalid_card_numbers": 0,
        "invalid_labels": 0,
        "invalid_timestamps": 0,
        "timestamp_min": None,
        "timestamp_max": None,
        "timestamp_decreases": 0,
        "same_timestamp_adjacent": 0,
        "negative_amounts": 0,
        "zero_amounts": 0,
        "invalid_amounts": 0,
        "invalid_coordinates": 0,
        "invalid_dob": 0,
        "dob_after_transaction": 0,
        "unix_time_mismatch_over_1s": 0,
        "unix_offset_seconds": Counter(),
        "unix_timestamp_min_utc": None,
        "unix_timestamp_max_utc": None,
        "unix_timestamp_decreases": 0,
        "unix_matches_timestamp_plus_7y": 0,
        "time_fields_comparable_rows": 0,
    }


def _update_file(path: Path, chunksize: int) -> dict[str, Any]:
    stats = _new_stats()
    previous_timestamp = None
    previous_unix_timestamp = None
    dtype = {CARD: "string", ID: "string", "zip": "string"}

    for chunk in pd.read_csv(path, chunksize=chunksize, dtype=dtype, low_memory=False):
        if not stats["columns"]:
            stats["columns"] = [str(c) for c in chunk.columns]
            stats["dtypes"] = {str(c): str(t) for c, t in chunk.dtypes.items()}

        n = len(chunk)
        stats["rows"] += n
        nulls = chunk.isna().sum()
        for col, count in nulls.items():
            stats["missing"][str(col)] += int(count)
        for col in chunk.select_dtypes(include=["object", "string"]).columns:
            blanks = chunk[col].astype("string").str.strip().eq("").fillna(False).sum()
            if blanks:
                stats["blank_strings"][str(col)] += int(blanks)

        # Hashes are retained only in memory; neither identifiers nor row values are logged.
        row_hashes = pd.util.hash_pandas_object(chunk, index=False).to_numpy(dtype="uint64")
        for fingerprint in row_hashes:
            key = int(fingerprint)
            if key in stats["row_fingerprints"]:
                stats["duplicate_rows"] += 1
            else:
                stats["row_fingerprints"].add(key)

        if ID in chunk:
            ids = chunk[ID].astype("string")
            invalid_ids = ids.isna() | ids.str.strip().eq("").fillna(True)
            stats["invalid_transaction_ids"] += int(invalid_ids.sum())
            for value in ids[~invalid_ids]:
                key = str(value)
                if key in stats["transaction_ids"]:
                    stats["duplicate_transaction_ids"] += 1
                else:
                    stats["transaction_ids"].add(key)

        if TARGET in chunk:
            labels = pd.to_numeric(chunk[TARGET], errors="coerce")
            valid = labels.isin([0, 1])
            stats["invalid_labels"] += int((~valid).sum())
            stats["labels"].update({str(int(k)): int(v) for k, v in labels[valid].value_counts().items()})

        if CARD in chunk:
            cards = chunk[CARD].astype("string").str.strip()
            valid_card = cards.notna() & cards.str.fullmatch(r"\d{12,19}").fillna(False)
            stats["invalid_card_numbers"] += int((~valid_card).sum())
            stats["card_ids"].update(cards[valid_card].astype(str).unique().tolist())
            if TARGET in chunk:
                fraud_rows = pd.to_numeric(chunk[TARGET], errors="coerce").eq(1) & valid_card
                stats["fraud_card_ids"].update(cards[fraud_rows].astype(str).unique().tolist())

        categorical_columns = [c for c in ("merchant", "category", "gender", "city", "state", "job") if c in chunk]
        for col in categorical_columns:
            vals = chunk[col].dropna().astype(str).unique().tolist()
            stats["categorical_values"].setdefault(col, set()).update(vals)

        ts = pd.to_datetime(chunk[TIMESTAMP], errors="coerce") if TIMESTAMP in chunk else pd.Series(pd.NaT, index=chunk.index)
        stats["invalid_timestamps"] += int(ts.isna().sum())
        valid_ts = ts.dropna()
        if not valid_ts.empty:
            local_min, local_max = valid_ts.min(), valid_ts.max()
            stats["timestamp_min"] = min(filter(None, [stats["timestamp_min"], local_min.isoformat()]), default=local_min.isoformat())
            stats["timestamp_max"] = max(filter(None, [stats["timestamp_max"], local_max.isoformat()]), default=local_max.isoformat())
            values = valid_ts.to_numpy()
            if len(values) > 1:
                stats["timestamp_decreases"] += int((values[1:] < values[:-1]).sum())
                stats["same_timestamp_adjacent"] += int((values[1:] == values[:-1]).sum())
            if previous_timestamp is not None:
                stats["timestamp_decreases"] += int(valid_ts.iloc[0] < previous_timestamp)
                stats["same_timestamp_adjacent"] += int(valid_ts.iloc[0] == previous_timestamp)
            previous_timestamp = valid_ts.iloc[-1]

        if "amt" in chunk:
            amount = pd.to_numeric(chunk["amt"], errors="coerce")
            stats["invalid_amounts"] += int((amount.isna() | ~amount.map(math.isfinite)).sum())
            stats["negative_amounts"] += int((amount < 0).sum())
            stats["zero_amounts"] += int((amount == 0).sum())

        coord_pairs = (("lat", -90, 90), ("long", -180, 180), ("merch_lat", -90, 90), ("merch_long", -180, 180))
        bad_coord = pd.Series(False, index=chunk.index)
        for col, lo, hi in coord_pairs:
            if col in chunk:
                value = pd.to_numeric(chunk[col], errors="coerce")
                bad_coord |= value.isna() | (value < lo) | (value > hi)
        stats["invalid_coordinates"] += int(bad_coord.sum())

        if "dob" in chunk and TIMESTAMP in chunk:
            dob = pd.to_datetime(chunk["dob"], errors="coerce")
            stats["invalid_dob"] += int(dob.isna().sum())
            stats["dob_after_transaction"] += int((dob.notna() & ts.notna() & (dob > ts)).sum())

        if "unix_time" in chunk and TIMESTAMP in chunk:
            unix = pd.to_numeric(chunk["unix_time"], errors="coerce")
            # Pandas 3 infers datetime64[s/us/ms/ns] from input precision. Normalize
            # before converting to integers; otherwise seconds can be mistaken for ns.
            parsed_seconds = _datetime_epoch_seconds(ts)
            comparable = ts.notna() & unix.notna()
            delta = parsed_seconds[comparable] - unix[comparable]
            stats["unix_time_mismatch_over_1s"] += int((delta.abs() > 1).sum())
            stats["time_fields_comparable_rows"] += int(comparable.sum())
            stats["unix_offset_seconds"].update(delta.astype("int64").tolist())
            unix_values = unix[comparable].astype("int64")
            if not unix_values.empty:
                unix_dates = pd.to_datetime(unix_values, unit="s", utc=True)
                first_unix, last_unix = int(unix_values.iloc[0]), int(unix_values.iloc[-1])
                stats["unix_timestamp_decreases"] += int((unix_values.diff().dropna() < 0).sum())
                if previous_unix_timestamp is not None:
                    stats["unix_timestamp_decreases"] += int(first_unix < previous_unix_timestamp)
                previous_unix_timestamp = last_unix
                stats["unix_timestamp_min_utc"] = min(filter(None, [stats["unix_timestamp_min_utc"], unix_dates.min().isoformat()]), default=unix_dates.min().isoformat())
                stats["unix_timestamp_max_utc"] = max(filter(None, [stats["unix_timestamp_max_utc"], unix_dates.max().isoformat()]), default=unix_dates.max().isoformat())
                reconstructed = unix_dates.dt.tz_localize(None) + pd.DateOffset(years=7)
                stats["unix_matches_timestamp_plus_7y"] += int(reconstructed.eq(ts[comparable]).sum())

    stats["missing"] = dict(stats["missing"])
    stats["blank_strings"] = dict(stats["blank_strings"])
    stats["labels"] = dict(stats["labels"])
    stats["unix_offset_seconds"] = {str(k): int(v) for k, v in stats["unix_offset_seconds"].items()}
    stats["cardinality"] = {c: len(v) for c, v in stats.pop("categorical_values").items()}
    return stats


def run_audit(raw_dir: Path | None = None, output_root: Path | None = None, chunksize: int = 50_000) -> dict[str, Any]:
    raw_dir = raw_dir or ROOT / "data" / "raw"
    output_root = output_root or ROOT
    files: dict[str, Any] = {}
    for filename in RAW_FILES:
        path = raw_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required raw dataset is missing: {path.name}")
        info = _update_file(path, chunksize)
        info["size_bytes"] = path.stat().st_size
        info["sha256"] = sha256_file(path)
        info["expected_rows"] = EXPECTED_ROWS[filename]
        info["row_count_matches_reference"] = info["rows"] == EXPECTED_ROWS[filename]
        files[filename] = info

    train, test = files[RAW_FILES[0]], files[RAW_FILES[1]]
    train_cols, test_cols = set(train["columns"]), set(test["columns"])
    shared_ids = train["transaction_ids"] & test["transaction_ids"]
    shared_cards = train["card_ids"] & test["card_ids"]
    for info in files.values():
        info["unique_card_count"] = len(info["card_ids"])
        info["fraud_card_count"] = len(info["fraud_card_ids"])
        info.pop("row_fingerprints", None)
    # Do not put raw card IDs or transaction IDs in outputs.
    train["transaction_ids"] = None
    test["transaction_ids"] = None
    train["card_ids"] = None
    test["card_ids"] = None
    train["fraud_card_ids"] = None
    test["fraud_card_ids"] = None

    timestamp_overlap = bool(
        train["timestamp_max"] and test["timestamp_min"]
        and pd.Timestamp(test["timestamp_min"]) <= pd.Timestamp(train["timestamp_max"])
    )
    findings = []
    findings.append({"status": "PASS" if train_cols == test_cols else "BLOCKER", "check": "schema_match", "detail": "Both files have the same columns." if train_cols == test_cols else "Column sets differ between raw files."})
    for filename, info in files.items():
        findings.append({"status": "PASS" if info["row_count_matches_reference"] else "WARNING", "check": f"reference_rows:{filename}", "detail": f"Observed {info['rows']:,}; reference {info['expected_rows']:,}."})
        findings.append({"status": "BLOCKER" if info["duplicate_transaction_ids"] or info["invalid_transaction_ids"] else "PASS", "check": f"transaction_id_integrity:{filename}", "detail": f"Duplicate IDs={info['duplicate_transaction_ids']:,}; missing/blank IDs={info['invalid_transaction_ids']:,}."})
        findings.append({"status": "BLOCKER" if info["invalid_labels"] else "PASS", "check": f"label_domain:{filename}", "detail": f"Invalid/missing labels={info['invalid_labels']:,}."})
        findings.append({"status": "BLOCKER" if info["invalid_timestamps"] else "PASS", "check": f"timestamp_parse:{filename}", "detail": f"Unparseable timestamps={info['invalid_timestamps']:,}."})
        findings.append({"status": "WARNING" if info["invalid_card_numbers"] else "PASS", "check": f"card_number_format:{filename}", "detail": f"Missing, non-digit, or shorter than 12-digit identifiers={info['invalid_card_numbers']:,}; values are preserved as strings and not used as model inputs."})
        findings.append({"status": "WARNING" if info["timestamp_decreases"] else "PASS", "check": f"source_timestamp_order:{filename}", "detail": f"Timestamp decreases in original row order={info['timestamp_decreases']:,}; the preprocessor sorts by parsed timestamp."})
    findings.append({"status": "BLOCKER" if shared_ids else "PASS", "check": "cross_file_transaction_ids", "detail": f"Shared transaction IDs={len(shared_ids):,}."})
    findings.append({"status": "BLOCKER" if timestamp_overlap else "PASS", "check": "test_after_train", "detail": f"train max={train['timestamp_max']}; test min={test['timestamp_min']}; strict ordering={not timestamp_overlap}."})
    time_matches_7y = all(
        info["time_fields_comparable_rows"] == info["rows"] == info["unix_matches_timestamp_plus_7y"]
        and info["unix_timestamp_decreases"] == 0
        for info in files.values()
    )
    if time_matches_7y:
        offset_seconds = [int(offset) for info in files.values() for offset in info["unix_offset_seconds"]]
        findings.append({
            "status": "WARNING",
            "check": "UNIX_TIME_STALE_BY_7_CALENDAR_YEARS",
            "code": "UNIX_TIME_STALE_BY_7_CALENDAR_YEARS",
            "detail": f"All {sum(info['time_fields_comparable_rows'] for info in files.values()):,} records reconstruct exactly when unix_time (seconds since epoch, interpreted UTC) is advanced by seven calendar years. Excluded from normalized data; raw CSVs remain unchanged. Offset seconds observed: {min(offset_seconds):,} to {max(offset_seconds):,}.",
        })
    else:
        findings.append({
            "status": "BLOCKER",
            "check": "UNIX_TIME_UNEXPLAINED_INCONSISTENCY",
            "code": "UNIX_TIME_UNEXPLAINED_INCONSISTENCY",
            "detail": "The raw timestamp fields do not match the verified seven-calendar-year stale-time pattern or unix_time is not chronological; investigate before processing.",
        })
    findings.append({"status": "PASS", "check": "cross_file_card_overlap", "detail": f"Shared cards={len(shared_cards):,}; card overlap alone is not leakage when prior history is used temporally."})
    manifest = {
        "files": files,
        "canonical_time_field": "trans_date_trans_time (parsed as timezone-naive timestamp)",
        "comparison": {
            "same_columns": train_cols == test_cols,
            "columns_only_in_train": sorted(train_cols - test_cols),
            "columns_only_in_test": sorted(test_cols - train_cols),
            "shared_transaction_ids": len(shared_ids),
            "shared_cards": len(shared_cards),
            "strict_test_after_train": not timestamp_overlap,
        },
        "findings": findings,
        "privacy": "No card numbers, names, street addresses, or raw row values are included in this manifest or the report.",
    }
    _write_outputs(manifest, output_root)
    return manifest


def _write_outputs(manifest: dict[str, Any], output_root: Path) -> None:
    docs, eda = output_root / "docs", output_root / "results" / "eda"
    docs.mkdir(parents=True, exist_ok=True)
    eda.mkdir(parents=True, exist_ok=True)
    serializable = json.loads(json.dumps(manifest, default=str))
    (docs / "data_manifest.json").write_text(json.dumps(serializable, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = ["# Data audit", "", "Full-file audit of `fraudTrain.csv` and `fraudTest.csv`. No direct identifiers or raw values are reported.", "", "Canonical event time is `trans_date_trans_time`, parsed as timezone-naive `timestamp`. Full-file checks verify `unix_time` exactly reconstructs this field only after adding seven calendar years; it is excluded from normalized data. See warning code `UNIX_TIME_STALE_BY_7_CALENDAR_YEARS`.", "", "## File inventory", "", "| File | Rows | Columns | Size (bytes) | SHA-256 |", "|---|---:|---:|---:|---|"]
    for filename, info in manifest["files"].items():
        lines.append(f"| `{filename}` | {info['rows']:,} | {len(info['columns'])} | {info['size_bytes']:,} | `{info['sha256']}` |")
    lines += ["", "## Findings", "", "| Status | Check | Detail |", "|---|---|---|"]
    for item in manifest["findings"]:
        lines.append(f"| **{item['status']}** | `{item['check']}` | {item['detail']} |")
    for filename, info in manifest["files"].items():
        lines += ["", f"## Quality summary: `{filename}`", "", f"- Target counts: `{info['labels']}`", f"- Duplicate complete rows: {info['duplicate_rows']:,}", f"- Duplicate transaction IDs: {info['duplicate_transaction_ids']:,}", f"- Card identifiers outside the 12-19 digit PAN-like range: {info['invalid_card_numbers']:,} (preserved as strings; synthetic IDs may not be actual PANs)", f"- Canonical text timestamp range: {info['timestamp_min']} to {info['timestamp_max']}", f"- Source timestamp decreases in row order: {info['timestamp_decreases']:,}", f"- Adjacent equal timestamps: {info['same_timestamp_adjacent']:,}", f"- Unix epoch timestamp range: {info['unix_timestamp_min_utc']} to {info['unix_timestamp_max_utc']}", f"- `trans_date_trans_time` minus `unix_time` offsets (seconds): `{info['unix_offset_seconds']}`", f"- Rows reconstructed exactly after adding seven calendar years to UTC unix_time: {info['unix_matches_timestamp_plus_7y']:,}/{info['time_fields_comparable_rows']:,}", f"- unix_time decreases in source order: {info['unix_timestamp_decreases']:,}", f"- Negative/zero/invalid amounts: {info['negative_amounts']:,}/{info['zero_amounts']:,}/{info['invalid_amounts']:,}", f"- Invalid coordinates: {info['invalid_coordinates']:,}", f"- Invalid or future DOB: {info['invalid_dob']:,}/{info['dob_after_transaction']:,}", f"- Missing values by column: `{info['missing']}`", f"- Blank strings by column: `{info['blank_strings']}`"]
    (docs / "data_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    quality = []
    classes = []
    for filename, info in manifest["files"].items():
        for column, count in info["missing"].items():
            quality.append({"dataset": filename, "check": "missing", "field": column, "count": count, "rate": count / info["rows"] if info["rows"] else None})
        for check in ("duplicate_rows", "duplicate_transaction_ids", "invalid_transaction_ids", "invalid_card_numbers", "invalid_labels", "invalid_timestamps", "negative_amounts", "zero_amounts", "invalid_amounts", "invalid_coordinates", "invalid_dob", "dob_after_transaction"):
            quality.append({"dataset": filename, "check": check, "field": "", "count": info[check], "rate": info[check] / info["rows"] if info["rows"] else None})
        fraud = int(info["labels"].get("1", 0)); normal = int(info["labels"].get("0", 0)); total = normal + fraud
        classes.append({"dataset": filename, "normal": normal, "fraud": fraud, "total": total, "fraud_rate": fraud / total if total else None, "normal_to_fraud_ratio": normal / fraud if fraud else None, "unique_cards": info["unique_card_count"], "fraud_cards": info["fraud_card_count"]})
    pd.DataFrame(quality).to_csv(eda / "data_quality_summary.csv", index=False)
    pd.DataFrame(classes).to_csv(eda / "class_distribution.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--chunksize", type=int, default=50_000)
    args = parser.parse_args()
    manifest = run_audit(args.raw_dir, args.output_root, args.chunksize)
    print(json.dumps({"findings": manifest["findings"], "files": {k: {"rows": v["rows"], "sha256": v["sha256"]} for k, v in manifest["files"].items()}}, indent=2))


if __name__ == "__main__":
    main()
