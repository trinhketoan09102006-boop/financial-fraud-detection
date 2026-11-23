"""Reproducible entry point for audit, preprocessing, split, EDA, and mock stages."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

from .audit import ROOT, run_audit
from .eda import run_eda
from .generate_mock import generate_mock
from .preprocess import preprocess
from .split import create_splits


def run(stage: str, force: bool = False, mock_rows_per_split: int = 100, cutoff_policy: str = "nearest_row_count") -> dict:
    started = time.perf_counter()
    results = {}
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    stages = ["audit", "preprocess", "split", "eda"] if stage == "all" else [stage]
    if stage == "mock":
        data, manifest = generate_mock(rows_per_split=mock_rows_per_split)
        results["mock"] = {"rows": len(data), "splits": manifest["split"].nunique()}
    else:
        if stage in {"preprocess", "split", "eda"}:
            report = run_audit()
            blockers = [item for item in report["findings"] if item["status"] == "BLOCKER"]
            if blockers:
                raise RuntimeError(f"Audit reported blockers; stage={stage} was not run: {blockers}")
        for name in stages:
            stage_start = time.perf_counter()
            logging.info("START stage=%s", name)
            if name == "audit":
                report = run_audit()
                blockers = [item for item in report["findings"] if item["status"] == "BLOCKER"]
                if blockers:
                    raise RuntimeError(f"Audit reported blockers; later stages stopped: {blockers}")
                outcome = {"rows": {k: v["rows"] for k, v in report["files"].items()}, "blockers": len(blockers)}
            elif name == "preprocess":
                frame = preprocess(force=force, validate_audit=False)
                outcome = {"rows": len(frame), "columns": len(frame.columns)}
            elif name == "split":
                outcome = create_splits(force=force, validate_audit=False, cutoff_policy=cutoff_policy)
            elif name == "eda":
                outcome = run_eda(validate_audit=False)
            else:
                raise ValueError(f"Unsupported stage: {name}")
            results[name] = {"elapsed_seconds": round(time.perf_counter() - stage_start, 3), "result": outcome}
            logging.info("DONE stage=%s elapsed_seconds=%.3f result=%s", name, time.perf_counter() - stage_start, json.dumps(outcome, default=str))
    results["total_elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["audit", "preprocess", "split", "eda", "all", "mock"], required=True)
    parser.add_argument("--force", action="store_true", help="Replace existing processed/split artifacts intentionally.")
    parser.add_argument("--mock-rows-per-split", type=int, default=100)
    parser.add_argument("--cutoff-policy", choices=["legacy", "nearest_row_count"], default="nearest_row_count")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.stage, args.force, args.mock_rows_per_split, args.cutoff_policy), indent=2, default=str))
    except Exception as exc:
        logging.exception("Pipeline stopped: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
