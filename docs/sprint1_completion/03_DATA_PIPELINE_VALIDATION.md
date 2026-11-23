# Data pipeline validation

## Environment

- Python 3.13.7
- pandas 2.2.3
- PyArrow 22.0.0
- Jupyter / nbconvert 7.16.6; ipykernel 6.30.1
- `pip check`: no broken requirements

Pandas 3 was unavailable. The datetime-unit regression covers second, millisecond, microsecond, and nanosecond units under installed pandas.

## Current `nearest_row_count` run

In the `sprint1-completion` worktree, the full pipeline ran after switching the default policy:

```powershell
python -m src.data.pipeline --stage all
```

- Exit code: 0; elapsed about 90.926 seconds.
- Policy/cutoff: `nearest_row_count`, `2020-03-06T07:16:43`.
- Rows: train 1,037,340; validation 259,335; test 555,719.
- Split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.
- Raw checksums remained train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`, test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.
- Normalized Parquet SHA-256 remained `60efdcdbb59aa1e503fc8b2ddb023d3d0bc84d611d176ec8b71f7713ecb66e30`.

All eight compared outputs matched the independently saved nearest-row-count proposal byte-for-byte: train/validation/test Parquet, manifest, split metadata, `configs/split.yaml`, `docs/split_report.md`, and `results/eda/split_summary.csv`. Current output hashes are recorded in `07_TRUNG_FEATURE_ENGINEERING_HANDOFF.md`. The full log is outside the repository at `sprint1_completion_evidence_20261122/pipeline_nearest_row_count_20261123.log`.

## Prior two-run reproducibility evidence

An earlier isolated validation project ran the pipeline twice against the former published split. Both runs exited 0 and the 33 checked outputs matched byte-for-byte, including the former split hash `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255`. Those runs establish reproducibility for the historical policy only; they are not represented as two independent executions of the newly selected policy. The current nearest-policy result was separately checked against the saved proposal artifacts as described above.

The earlier validation project was `sprint1_completion_validation`; it read raw inputs by directory junction and wrote generated data outside the original project. Its logs and hash snapshots are under `sprint1_completion_evidence_20261122`.

## Raw input audit and normalized output

| File | Rows | Size | SHA-256 |
|---|---:|---:|---|
| `data/raw/fraudTrain.csv` | 1,296,675 | 351,238,196 bytes | `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d` |
| `data/raw/fraudTest.csv` | 555,719 | 150,354,339 bytes | `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0` |

The audit found no blocker: no duplicate/missing transaction IDs, cross-file transaction-ID overlap, invalid labels, or invalid timestamps. It recorded 11-digit card identifiers and one source-order timestamp decrease in train. Raw checksums were unchanged after pipeline and notebook execution.

Normalized output contains 1,852,394 rows and 25 columns. `timestamp` and `dob` are Arrow `timestamp[ns]` with no timezone. `trans_num` and `cc_num` are strings; `trans_num` is unique/non-null; `is_fraud` is `int8`. `unix_time`, `first`, `last`, and `street` are absent. No row removal, imputation, or resampling occurred. The audit confirms epoch `unix_time` plus seven calendar years reconstructs the canonical text timestamp for all rows; `unix_time` remains excluded from normalized data.

## Artifact location and limits

The current generated Parquet outputs are physically in this worktree's `data/processed/` and `data/splits/` folders. Git ignores them; they are untracked local verification artifacts and are not included in a source handoff. The raw inputs are required to recreate them. Keep these datasets out of the code review diff.
