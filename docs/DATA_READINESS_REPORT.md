# Data readiness report

## Decision summary

- **DATA_PIPELINE_READINESS: PASS** for local development and model input generation.
- **MODEL_INPUT_READINESS: PASS** for the validated temporal splits and declared baseline feature contract.
- **CURRENT_SPLIT: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`** using `nearest_row_count`, cutoff `2020-03-06T07:16:43`.
- **TEAM_HANDOFF_READINESS: CONDITIONAL** because GitHub remote state could not be fetched and generated Parquet artifacts remain local/ignored.
- **GIT_SAFETY_READINESS: PASS for this local review state**; no commit, push, merge, or tracking change was made.
- **OVERALL: CONDITIONAL_READY** for local review; publish/handoff requires review and a shared artifact path or reproducible access to raw data.

## Data checks

| Criterion | Status | Evidence |
|---|---|---|
| Full source read | PASS | Both files audited in full. |
| Source row counts | PASS | Train 1,296,675; test 555,719; total 1,852,394. |
| Labels | PASS | Train 7,506 fraud; test 2,145 fraud; all labels are 0/1. |
| Schema / IDs | PASS | Same 23 columns; no duplicate rows, duplicate/missing `trans_num`, or cross-file transaction ID overlap. |
| Canonical timestamp | PASS | `trans_date_trans_time`; all rows parse. Train has one source-order decrease, handled by timestamp sort. |
| `unix_time` root cause | PASS | Epoch seconds plus seven calendar years reconstruct canonical time across all 1,852,394 rows; excluded from normalized/model data. |
| Missing / numeric / coordinate / DOB checks | PASS | No missing values, invalid labels/timestamps, invalid amounts, invalid coordinates, or future DOBs. |
| Card identifier lengths | WARNING | 6,111 train and 2,708 test IDs are 11-digit strings; preserved for grouping, excluded from model features. |
| Processed table | PASS | 1,852,394 rows, 25 columns, unique `trans_num`, no `unix_time`, names, surname, or street fields. |
| Temporal split | PASS | Train 1,037,340; validation 259,335; test 555,719; cutoff `2020-03-06T07:16:43`; strict chronology, timestamp groups atomic, IDs disjoint. |
| Split hash | PASS | `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`; matches generated metadata and regression expectation. |
| EDA | PASS | Ten charts and aggregates regenerated from training split only. |
| Contract / mock / tests | PASS | Contract and 300-row synthetic mock validated; 14 pytest passed, 0 skipped. |
| Raw checksums | PASS | Train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`. |

## Split policy change

Toan requested the switch to `nearest_row_count` on 2026-11-23. The former hash `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255` is historical. Exactly one transaction (`408a69cd781df5546489ecb28a2007ea`, timestamp `2020-03-06T07:15:17`) moved from validation to train. Current counts are train 1,037,340 and validation 259,335; test is unchanged. All downstream split artifacts and EDA were regenerated.

## Arrow schema validation

All 25 Parquet fields were compared with `configs/data_schema.yaml`. Contract text columns are stored as Arrow `string`, timestamps as timezone-naive `timestamp[ns]`. Regression coverage forces `large_string` input and checks the written Parquet type.

## Git LFS and artifact location

The raw CSVs remain LFS-tracked in the repository history, with the checksums above. The `.gitattributes` rule is scoped to `data/raw/*.csv`; `.gitignore` excludes raw, processed, and split data. In the `toan` worktree, generated Parquet outputs are physically present under `data/processed/` and `data/splits/`, but ignored and untracked. Do not stage them. Their presence allows local integration tests and notebook execution; teammates cannot access them unless they recreate the pipeline or receive them through an approved data channel.

A remote fetch previously returned `Repository not found`; remote branch freshness remains unverified. No history/index/LFS tracking changes were made.

## Remaining handoff conditions

1. Review the updated split hash and one-record membership change with downstream owners before model outputs are compared across split versions.
2. Provide or restore `TOAN_SPRINT1_REMAINING_WORK.md`; it is absent and was not read or audited.
3. Restore remote read access and verify GitHub branch state before any publication action.
4. Share/recreate ignored Parquet artifacts for downstream use; do not add raw or processed transaction datasets to a code review commit.
