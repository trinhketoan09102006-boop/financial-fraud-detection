# Final Sprint 1 validation

## Environment

- Python 3.13.7
- pandas 2.2.3
- PyArrow 22.0.0
- pytest 9.2.0
- `python -m pip check`: PASS, no broken requirements
- `python -m compileall -q src tests`: PASS

## Pipeline and data contract

The full pipeline was run twice on branch `toan` with `nearest_row_count`. Run 1 exited 0. Run 2 used `--force` only after run 1 had been snapshotted under ignored `data/processed/.sprint1_run1_20261123/`; it also exited 0. Both runs produced identical SHA-256 values for all 34 compared outputs: normalized Parquet, splits, manifest, split metadata, config, audit/preprocessing/split/EDA reports, and EDA tables/figures. See `10_reproducibility_comparison.json` and the two pipeline logs.

| Output | Rows | SHA-256 |
|---|---:|---|
| Processed | 1,852,394 | `60efdcdbb59aa1e503fc8b2ddb023d3d0bc84d611d176ec8b71f7713ecb66e30` |
| Train | 1,037,340 | `aefcebfe4a8c07bd2ea9eaef3d65edc493244c3dd6dcaf4f5eb694aa9004bd55` |
| Validation | 259,335 | `9feecd921fdaa08c876d8ea902af1072483ad45c68cb8152bddb65a92b56d4c7` |
| Test | 555,719 | `43f3b72e486d9b544fc4963f61d4b8d7ac4531507f81007f1ba554f16f854570` |
| Split manifest | 1,852,394 | `b8559100aaa195fe5ffe80d1a2c15360578c5ad456a7cdba5facd7eaaa0848bc` |

- Policy: `nearest_row_count`; cutoff `2020-03-06T07:16:43`.
- Split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8` in config and metadata.
- All 25 Arrow fields match the contract exactly; text types are `string`, timestamps are timezone-naive `timestamp[ns]`.
- `trans_num` is unique and non-null; all 1,852,394 raw transaction IDs join one-to-one to processed records, and `cc_num` is preserved exactly as a string.
- Labels remain 0/1; `unix_time` is excluded; train < validation < test chronology is strict, timestamp groups remain atomic, IDs are disjoint, and the manifest covers all rows.
- Raw SHA-256 stayed unchanged: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.

## Tests and notebook

- Full command: `python -m pytest -q -rs`.
- Result after pipeline artifacts existed: **14 passed, 0 failed, 0 skipped**, exit code 0. One third-party AnyIO `PytestRemovedIn10Warning` remains.
- This includes the full-data integration test and the new Arrow `large_string` regression.
- Notebook `notebooks/01_data_understanding.ipynb` executed separately against the new split: 2/2 code cells completed, no cell errors, nbconvert exit code 0. The executed copy is kept in the ignored local evidence folder; the source notebook was not overwritten. A non-fatal Windows ZeroMQ Proactor event-loop warning was emitted.
- EDA ran on train only and generated ten charts. It uses the target for descriptive analysis, not for creating model features.

## Git, LFS, and blockers

- Current branch remains `toan`, HEAD `0515b4b3c87431e1dae39c50f012b211385442d6`.
- Raw files remain LFS-tracked; `git lfs fsck` passed. No LFS rules, raw files, refs, or history were changed.
- `.gitignore` excludes generated processed/split files. Parquet outputs remain local and untracked; only `.gitkeep` in those folders is tracked.
- No commit, push, merge, branch creation, reset, rebase, cleanup, or remote fetch was performed.
- The locally cached remote refs show `origin/toan=0515b4b` and `origin/main=9648beb`; their freshness was not checked during this task.
- `TOAN_SPRINT1_FINAL_FIX_HANDOFF.md` was absent. It was not read; the implementation followed the supplied F01-F06 requirements.
- Git reports a pre-existing linked worktree registration as `prunable`; it was not changed.

## Handoff status

`READY_FOR_TRUNG: CONDITIONAL`. The artifact paths, hashes, schema, split policy, and rebuild steps are documented in `07_TRUNG_FEATURE_ENGINEERING_HANDOFF.md`. Trung can consume the data from this same workspace. For another machine, he must recreate from authorized raw inputs or use an approved access-controlled artifact transfer and verify the listed hashes.

`READY_TO_COMMIT: YES, after review`. All code, documentation, and reports remain uncommitted on `toan`. No publication action was taken.
