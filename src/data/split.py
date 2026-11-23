"""Build reproducible, timestamp-grouped train/validation/test splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from .audit import ROOT, run_audit, sha256_file


def stable_split_hash(manifest: pd.DataFrame) -> str:
    ordered = manifest.sort_values(["trans_num", "split"], kind="mergesort")
    digest = hashlib.sha256()
    for row in ordered.itertuples(index=False):
        digest.update(str(row.trans_num).encode("utf-8"))
        digest.update(b"\t")
        digest.update(str(row.split).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def choose_timestamp_cutoff(group_sizes: pd.Series, target_train_rows: int, policy: str = "nearest_row_count") -> pd.Timestamp:
    """Choose the first validation timestamp without splitting timestamp groups.

    ``nearest_row_count`` selects the legal boundary whose training row count is
    closest to the target. ``legacy`` remains available to reproduce the former
    published split when explicitly requested.
    """
    if len(group_sizes) < 2:
        raise ValueError("At least two timestamp groups are required for a temporal split.")
    cumulative = group_sizes.cumsum()
    if policy == "legacy":
        # Historical behavior: this preserves the published split hash, although
        # it can drop the boundary group from the training rows.
        candidates = cumulative[(cumulative > 0) & (cumulative < int(group_sizes.sum()))]
        if candidates.empty:
            raise ValueError("Not enough unique timestamps to create a temporal split.")
        return pd.Timestamp(candidates.sub(target_train_rows).abs().idxmin())
    if policy == "nearest_row_count":
        legal_train_counts = cumulative.iloc[:-1]
        if legal_train_counts.empty:
            raise ValueError("Not enough unique timestamps to create a temporal split.")
        last_train_timestamp = pd.Timestamp(legal_train_counts.sub(target_train_rows).abs().idxmin())
        position = group_sizes.index.get_loc(last_train_timestamp)
        return pd.Timestamp(group_sizes.index[position + 1])
    raise ValueError(f"Unsupported cutoff policy: {policy}")


def _write_parquet(frame: pd.DataFrame, path: Path, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to replace existing split: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    try:
        frame.to_parquet(temp, index=False, compression="zstd")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def create_splits(processed_path: Path | None = None, raw_dir: Path | None = None, output_dir: Path | None = None, force: bool = False, train_fraction: float = 0.8, project_root: Path | None = None, validate_audit: bool = True, cutoff_policy: str = "nearest_row_count") -> dict:
    processed_path = processed_path or ROOT / "data" / "processed" / "transactions.parquet"
    raw_dir = raw_dir or ROOT / "data" / "raw"
    output_dir = output_dir or ROOT / "data" / "splits"
    project_root = project_root or ROOT
    if validate_audit:
        audit = run_audit(raw_dir=raw_dir, output_root=project_root)
        blockers = [item for item in audit["findings"] if item["status"] == "BLOCKER"]
        if blockers:
            raise RuntimeError(f"Split stopped because audit reported BLOCKER findings: {blockers}")
    if not 0.5 <= train_fraction < 1:
        raise ValueError("train_fraction must be in [0.5, 1).")
    if not processed_path.is_file():
        raise FileNotFoundError(f"Run preprocessing first: {processed_path}")
    existing = [output_dir / f"{name}.parquet" for name in ("train", "validation", "test", "split_manifest")]
    if not force and any(path.exists() for path in existing):
        raise FileExistsError("At least one split output already exists; use --force only when intentionally rebuilding.")

    data = pd.read_parquet(processed_path)
    if data["trans_num"].isna().any() or data["trans_num"].duplicated().any():
        raise ValueError("Input must have unique, non-null trans_num.")
    source_train = data.loc[data["source_dataset"].eq("fraudTrain")].sort_values("timestamp", kind="mergesort")
    test = data.loc[data["source_dataset"].eq("fraudTest")].sort_values("timestamp", kind="mergesort")
    if source_train.empty or test.empty:
        raise ValueError("Expected rows from both source datasets.")
    target = int(len(source_train) * train_fraction)
    group_sizes = source_train.groupby("timestamp", sort=True, observed=True).size()
    cutoff = choose_timestamp_cutoff(group_sizes, target, policy=cutoff_policy)
    train = source_train.loc[source_train["timestamp"] < cutoff].copy()
    validation = source_train.loc[source_train["timestamp"] >= cutoff].copy()

    if train.empty or validation.empty:
        raise ValueError("Temporal cutoff produced an empty split.")
    if train["timestamp"].max() >= validation["timestamp"].min():
        raise AssertionError("A shared timestamp crossed the train/validation boundary.")
    if validation["timestamp"].max() >= test["timestamp"].min():
        raise RuntimeError("BLOCKER: fraudTest is not strictly later than validation; no automatic reassignment is allowed.")

    split_frames = {"train": train, "validation": validation, "test": test}
    manifest = pd.concat([part[["trans_num"]].assign(split=name) for name, part in split_frames.items()], ignore_index=True)
    if manifest["trans_num"].duplicated().any() or len(manifest) != len(data):
        raise AssertionError("Split assignment must cover every transaction exactly once.")
    split_hash = stable_split_hash(manifest)
    raw_hashes = {name: sha256_file(raw_dir / name) for name in ("fraudTrain.csv", "fraudTest.csv")}

    for name, part in split_frames.items():
        _write_parquet(part.sort_values(["timestamp", "trans_num"], kind="mergesort"), output_dir / f"{name}.parquet", force)
    _write_parquet(manifest.sort_values(["trans_num", "split"], kind="mergesort"), output_dir / "split_manifest.parquet", force)

    summary = []
    for name, part in split_frames.items():
        fraud = int(part["is_fraud"].sum())
        summary.append({
            "split": name, "rows": len(part), "normal": len(part) - fraud, "fraud": fraud,
            "fraud_rate": fraud / len(part), "unique_cards": int(part["cc_num"].nunique()),
            "timestamp_min": part["timestamp"].min().isoformat(), "timestamp_max": part["timestamp"].max().isoformat(),
        })
    eda_dir = project_root / "results" / "eda"
    eda_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(eda_dir / "split_summary.csv", index=False)
    meta = {
        "train_fraction_requested": train_fraction,
        "cutoff_policy": cutoff_policy,
        "canonical_time_field": "timestamp (parsed from trans_date_trans_time)",
        "cutoff_timestamp": cutoff.isoformat(),
        "split_hash": split_hash,
        "source_sha256": raw_hashes,
        "processed_sha256": sha256_file(processed_path),
        "rows": {name: len(part) for name, part in split_frames.items()},
        "ordering": "timestamp ascending; trans_num is only a deterministic tie-breaker",
        "validation_test_usage": "validation and test are not sampled; test was preserved from fraudTest.csv",
    }
    (project_root / "configs").mkdir(parents=True, exist_ok=True)
    (project_root / "configs" / "split.yaml").write_text(
        "# Generated by src.data.split; split manifest is the source of truth.\n"
        + "canonical_time_field: timestamp # parsed from trans_date_trans_time\n"
        + "train_fraction_requested: " + str(train_fraction) + "\n"
        + "cutoff_policy: '" + cutoff_policy + "'\n"
        + "cutoff_timestamp: '" + cutoff.isoformat() + "'\n"
        + "split_hash: '" + split_hash + "'\n"
        + "source_sha256:\n"
        + "  fraudTrain.csv: '" + raw_hashes["fraudTrain.csv"] + "'\n"
        + "  fraudTest.csv: '" + raw_hashes["fraudTest.csv"] + "'\n"
        + "rows:\n" + "".join(f"  {name}: {len(part)}\n" for name, part in split_frames.items()),
        encoding="utf-8",
    )
    (output_dir / "split_metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    report_lines = ["# Temporal split report", "", f"- Requested train fraction of original training file: {train_fraction:.1%}.", f"- Cutoff policy: `{cutoff_policy}`.", f"- Timestamp cutoff (first validation timestamp): {cutoff.isoformat()}.", f"- Stable split hash: `{split_hash}`.", f"- Raw SHA-256: `{raw_hashes}`.", "- No random or stratified splitting; same-timestamp groups stay together.", "- fraudTest.csv is preserved wholly as test because its timestamps follow fraudTrain.csv.", "", "| Split | Rows | Normal | Fraud | Fraud rate | Cards | Min timestamp | Max timestamp |", "|---|---:|---:|---:|---:|---:|---|---|"]
    for row in summary:
        report_lines.append(f"| {row['split']} | {row['rows']:,} | {row['normal']:,} | {row['fraud']:,} | {row['fraud_rate']:.4%} | {row['unique_cards']:,} | {row['timestamp_min']} | {row['timestamp_max']} |")
    report_lines += ["", "The 80/20 boundary is chosen at the nearest whole timestamp group, so counts can differ slightly from the row-based target. Card overlap across splits is expected and permits use of observed prior history; transaction IDs remain disjoint."]
    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    (project_root / "docs" / "split_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return {"rows": {name: len(part) for name, part in split_frames.items()}, "split_hash": split_hash, "cutoff_timestamp": cutoff.isoformat(), "cutoff_policy": cutoff_policy, "summary": summary, "metadata": meta}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=ROOT / "data" / "processed" / "transactions.parquet")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "splits")
    parser.add_argument("--train-fraction", type=float, default=0.8)
    parser.add_argument("--cutoff-policy", choices=["legacy", "nearest_row_count"], default="nearest_row_count")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(json.dumps(create_splits(args.processed, args.raw_dir, args.output_dir, args.force, args.train_fraction, cutoff_policy=args.cutoff_policy), indent=2))


if __name__ == "__main__":
    main()
