# Feature Engineering handoff for Trung

## Readiness

`CONDITIONAL_READY`. The full processed dataset and splits exist in this local `financial-fraud-detection` worktree and have been validated against the schema and split contract. They are ignored by Git and are not delivered to another machine through this code diff. Trung can use them from this same workspace, or recreate them using the instructions below after obtaining the raw inputs.

## Canonical inputs

| Input | Path from repository root | Rows | SHA-256 |
|---|---|---:|---|
| Normalized transactions | `data/processed/transactions.parquet` | 1,852,394 | `60efdcdbb59aa1e503fc8b2ddb023d3d0bc84d611d176ec8b71f7713ecb66e30` |
| Train | `data/splits/train.parquet` | 1,037,340 | `aefcebfe4a8c07bd2ea9eaef3d65edc493244c3dd6dcaf4f5eb694aa9004bd55` |
| Validation | `data/splits/validation.parquet` | 259,335 | `9feecd921fdaa08c876d8ea902af1072483ad45c68cb8152bddb65a92b56d4c7` |
| Test | `data/splits/test.parquet` | 555,719 | `43f3b72e486d9b544fc4963f61d4b8d7ac4531507f81007f1ba554f16f854570` |
| Split manifest | `data/splits/split_manifest.parquet` | 1,852,394 | `b8559100aaa195fe5ffe80d1a2c15360578c5ad456a7cdba5facd7eaaa0848bc` |
| Split metadata | `data/splits/split_metadata.json` | n/a | `468b129fecf0dbff1557b1ac86e157639546427d3bc9df10f4084708dd0b4d3f` |

Current split policy is `nearest_row_count`; cutoff is `2020-03-06T07:16:43`; split hash is `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. The hash is repeated in `configs/split.yaml`, `data/splits/split_metadata.json`, and this handoff. `trans_date_trans_time` is canonical; `unix_time` is excluded because it is seven calendar years stale.

The normalized table has the exact 25-field contract schema. Text fields are Arrow `string`, not `large_string`; timestamps are timezone-naive `timestamp[ns]`. `trans_num` is unique/non-null. `cc_num` is preserved as a string. Raw SHA-256: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.

Environment used for validation: Python 3.13.7, pandas 2.2.3, PyArrow 22.0.0, pytest 9.2.0.

## Recreate and validate locally

From the repository root, with both raw LFS files available and no existing generated outputs:

```powershell
python -m src.data.pipeline --stage all
python -m pytest -q -rs
```

Expected split policy/hash and counts are checked by the integration test and stored in `configs/split.yaml` plus `data/splits/split_metadata.json`. If generated outputs already exist, preserve/verify them first; the pipeline refuses to overwrite without `--force`. Do not use `--force` on shared work without a backup.

To check the saved artifacts manually:

```powershell
python -c "import json; print(json.load(open('data/splits/split_metadata.json', encoding='utf-8'))['split_hash'])"
Get-FileHash data/processed/transactions.parquet,data/splits/train.parquet,data/splits/validation.parquet,data/splits/test.parquet,data/splits/split_manifest.parquet -Algorithm SHA256
```

## Local artifact sync for Trung

The Parquet files are local ignored artifacts; they are deliberately absent from Git. If Trung shares this same machine/workspace, read the listed paths directly. Otherwise, either obtain the two raw files through the approved data access route and run the two commands above in the same project revision, or transfer these generated Parquet files and `split_metadata.json` using an approved access-controlled data channel. Before feature work, compare each SHA-256, confirm the split hash, and keep raw/processed Parquet out of Git commits.

## Feature Engineering contract

1. `trans_num` is the one-to-one transaction join key; retain it on each output row.
2. Keep `cc_num` as a string and use it only to group same-card history; never pass it as a model feature.
3. For an anchor at `timestamp=t`, use only same-card records where `timestamp < t`.
4. Treat equal-timestamp transactions as a batch; none may use another event in that batch as history.
5. Observed prior train history may cross into validation/test under the data contract.
6. Never use `is_fraud` to make history features. Fit encoders, imputers, and other transforms on train only.
7. Do not assign a timezone or currency because the source does not specify them.

No Feature Engineering implementation was performed; this is an input and leakage-policy handoff only.
