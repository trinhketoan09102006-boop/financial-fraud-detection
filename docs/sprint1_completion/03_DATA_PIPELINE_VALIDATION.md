# Data pipeline validation

## Environment

- Python 3.13.7; pandas 2.2.3; PyArrow 22.0.0; pytest 9.2.0.
- `python -m pip check`: PASS.
- `python -m compileall -q src tests`: PASS.

## Full pipeline and reproducibility

The full pipeline ran twice on branch `toan` with `nearest_row_count`. Run 1:

```powershell
python -m src.data.pipeline --stage all
```

Run 2:

```powershell
python -m src.data.pipeline --stage all --force
```

Run 2 was performed after snapshotting Run 1 artifacts under the Git-ignored path `data/processed/.sprint1_run1_20261123/`. Both commands exited 0. SHA-256 matched byte-for-byte for all 34 files: normalized Parquet, all split Parquets and metadata, config, audit/preprocessing/split/EDA reports, and EDA tables/figures. See `10_reproducibility_comparison.json`; complete logs are `10_pipeline_execution.txt` and `10_pipeline_execution_run2.txt`.

- Processed: 1,852,394 rows; SHA-256 `60efdcdbb59aa1e503fc8b2ddb023d3d0bc84d611d176ec8b71f7713ecb66e30`.
- Train: 1,037,340; validation: 259,335; test: 555,719.
- Policy: `nearest_row_count`; cutoff `2020-03-06T07:16:43`.
- Split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

## Schema and data integrity

All 25 Parquet fields match `configs/data_schema.yaml`. Every contract text field has Arrow `string`; timestamps are timezone-naive `timestamp[ns]`. `trans_num` is unique and non-null. A full one-to-one join of all raw rows to the processed table confirmed `cc_num` is preserved exactly. Labels remain 0/1; `unix_time` is absent. Split chronology is strict, timestamp groups stay together, IDs are disjoint, and the manifest covers every row.

Raw checksums remained unchanged: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`. Detailed checks and hashes are in `10_pipeline_validation.json` and `10_artifact_hashes.json`.

## Tests and notebook

The final full suite result is **14 passed, 0 failed, 0 skipped**, exit code 0. The sole warning is the installed AnyIO plugin's third-party `PytestRemovedIn10Warning`. Full log: `10_pytest_final.txt`.

The notebook was executed separately after the pipeline. It exited 0, completed 2/2 code cells without cell errors, and used the new training split. An executed copy is under ignored `data/processed/.sprint1_backup_20261123/notebook_execution/`; the source notebook was not overwritten. The only notebook warning was a non-fatal ZeroMQ Proactor event-loop compatibility warning. See `10_notebook_execution.txt` and `10_notebook_validation.json`.
