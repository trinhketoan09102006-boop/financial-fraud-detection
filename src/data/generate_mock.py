"""Create a deterministic, synthetic transaction dataset for interface tests."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .audit import ROOT


def generate_mock(output_dir: Path | None = None, rows_per_split: int = 100, seed: int = 2026) -> tuple[pd.DataFrame, pd.DataFrame]:
    if rows_per_split < 10:
        raise ValueError("Use at least 10 rows per split to include both labels and repeated timestamps.")
    output_dir = output_dir or ROOT / "data" / "samples"
    rng = np.random.default_rng(seed)
    records = []
    split_names = ("train", "validation", "test")
    starts = pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"])
    merchants = [f"merchant_{i:02d}" for i in range(8)]
    categories = ["grocery", "travel", "online", "new_category"]
    for split_idx, split in enumerate(split_names):
        for i in range(rows_per_split):
            card_num = 100000000000 + (i % 12)
            # Include a previously unseen card in each later split.
            if split != "train" and i in (0, 1):
                card_num = 900000000000 + split_idx * 10 + i
            # Four-hour batches give more than seven days of history by default.
            ts = starts[split_idx] + pd.Timedelta(hours=(i // 2) * 4)
            fraud = int(i % 20 == 0 or i % 37 == 0)
            merchant = "merchant_new" if split == "test" and i == 3 else merchants[int(rng.integers(0, len(merchants)))]
            category = "new_category_test" if split == "test" and i == 4 else categories[int(rng.integers(0, len(categories)))]
            amt = 100_000.0 if split == "test" and i == 5 else float(rng.uniform(1, 450))
            records.append({
                "trans_num": f"mock-{split}-{i:04d}", "cc_num": str(card_num), "timestamp": ts,
                "amt": amt, "merchant": merchant, "category": category,
                "gender": str(rng.choice(["F", "M"])), "city": f"city_{i % 15}", "state": "CA",
                "zip": None if i == 7 else f"{90000 + i:05d}", "lat": 37.7, "long": -122.4,
                "city_pop": None if split == "validation" and i == 8 else 100_000,
                "dob": pd.Timestamp("1980-01-01") + pd.Timedelta(days=i % 1000), "job": f"job_{i % 10}",
                "unix_time": int(ts.timestamp()), "merch_lat": 37.8, "merch_long": -122.5,
                "is_fraud": fraud, "hour": ts.hour, "day_of_week": ts.dayofweek, "month": ts.month,
                "is_weekend": int(ts.dayofweek >= 5), "age_at_transaction": (ts - pd.Timestamp("1980-01-01")).days / 365.2425,
                "merchant_distance_km": 14.17, "source_dataset": "mock",
            })
    transactions = pd.DataFrame(records).sort_values(["timestamp", "trans_num"], kind="mergesort", ignore_index=True)
    manifest = transactions[["trans_num"]].copy()
    manifest["split"] = np.repeat(split_names, rows_per_split)
    manifest = manifest.sort_values("trans_num", kind="mergesort", ignore_index=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    transactions.to_csv(output_dir / "mock_transactions.csv", index=False)
    manifest.to_csv(output_dir / "mock_split_manifest.csv", index=False)
    (output_dir / "README.md").write_text(
        f"""# Mock transaction data

These {len(transactions)} rows are synthetic and generated with NumPy seed `{seed}`. They contain no records copied from the Sparkov CSVs and are for interface and pipeline tests only; they do not represent model performance.

        `mock_transactions.csv` follows the normalized transaction schema. `mock_split_manifest.csv` maps each unique `trans_num` to one time-ordered split. The default fixture spans more than seven days per split for 1h/24h/7d history tests and includes both labels, tied timestamps, unseen cards, new merchants/categories, a large amount, and nullable fields.
""", encoding="utf-8")
    return transactions, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "samples")
    parser.add_argument("--rows-per-split", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    data, manifest = generate_mock(args.output_dir, args.rows_per_split, args.seed)
    print(f"Generated {len(data)} synthetic transactions across {manifest['split'].nunique()} splits.")


if __name__ == "__main__":
    main()
