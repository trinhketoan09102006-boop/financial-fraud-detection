# Feature Engineering handoff for Trung

## Readiness

`CONDITIONAL_READY` for local use. The full pipeline has regenerated current split artifacts in this worktree and tests pass against them. Processed and split Parquet files are ignored/untracked local artifacts; they are not part of the review diff or available to another machine. Recreate them from the raw inputs or transfer through an approved data channel.

Worktree root: `financial-fraud-detection-sprint1 worktree`
Current split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`
Policy: `nearest_row_count`
Cutoff: `2020-03-06T07:16:43`

| Input | Local path | SHA-256 |
|---|---|---|
| Normalized table | `data/processed/transactions.parquet` | `60efdcdbb59aa1e503fc8b2ddb023d3d0bc84d611d176ec8b71f7713ecb66e30` |
| Train | `data/splits/train.parquet` | `aefcebfe4a8c07bd2ea9eaef3d65edc493244c3dd6dcaf4f5eb694aa9004bd55` |
| Validation | `data/splits/validation.parquet` | `9feecd921fdaa08c876d8ea902af1072483ad45c68cb8152bddb65a92b56d4c7` |
| Test | `data/splits/test.parquet` | `43f3b72e486d9b544fc4963f61d4b8d7ac4531507f81007f1ba554f16f854570` |
| Split manifest | `data/splits/split_manifest.parquet` | `b8559100aaa195fe5ffe80d1a2c15360578c5ad456a7cdba5facd7eaaa0848bc` |
| Split metadata | `data/splits/split_metadata.json` | `468b129fecf0dbff1557b1ac86e157639546427d3bc9df10f4084708dd0b4d3f` |

## Interface and policy

- Grain: one row per transaction; `trans_num` is a unique, non-null string join key.
- `cc_num` is a preserved string used only to group card history; never pass it as a model feature.
- `timestamp` is timezone-naive `timestamp[ns]`, parsed from `trans_date_trans_time`. Source timezone is unspecified; do not assign one without a documented decision.
- `is_fraud` is the target and must not enter history features.
- Split manifest fields: `trans_num`, `split`; it covers all 1,852,394 rows one-to-one.
- Current rows: train 1,037,340; validation 259,335; test 555,719. Chronology is strict and equal timestamps remain in one split.
- All feature/evaluation outputs must carry split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. Do not mix outputs built using the historical hash `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255`.
- Allowed history: same `cc_num`, event time strictly less than the anchor time. Treat events at an equal timestamp as a batch before updating state. History may cross from observed train into validation/test under the contract. Do not use labels in history.
- Fit feature transforms/encoders on train only; validation/test remain unchanged.

## Recreate and validate

With the raw inputs at `data/raw/` and no stale generated outputs, run:

```powershell
python -m src.data.pipeline --stage all
python -m pytest -q -rs
```

Expected split hash is recorded in `configs/split.yaml` and `data/splits/split_metadata.json`. The local artifacts are ignored and should not be staged. Current raw checksums: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.

Baseline model inputs are in `configs/base_features.yaml`. No history feature generation was implemented in Sprint 1. Sparkov is simulated, and currency/timezone are unspecified; do not interpret its results as production performance.
