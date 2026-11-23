# Sprint 1 Data Engineering completion summary

Date: 2026-11-23
Working branch: `sprint1-completion`
Baseline HEAD: `af693e0274ddfb9d7f4b57b13f6872b95680bfe9`

## Outcome

The `nearest_row_count` split is now the current policy in this worktree, per Toan's explicit request. The pipeline was rerun on the full Sparkov inputs, all dependent split/EDA outputs were regenerated, the notebook executed successfully, and the full suite passed with no skips. The current split hash is `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

| Item | Status | Evidence / remaining condition |
|---|---|---|
| T01 Temporal split cutoff | `PASS` | `nearest_row_count` is the default; cutoff `2020-03-06T07:16:43`; counts 1,037,340 / 259,335 / 555,719; current hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. |
| T02 Raw-to-processed pipeline | `PASS` | Full pipeline rerun exited 0; raw checksums and normalized parquet hash unchanged. |
| T03 EDA notebook | `PASS` | Executed separately after regeneration; 2/2 cells, nbconvert exit 0; ten charts. Non-fatal Windows ZeroMQ event-loop warning. |
| T04 Schema and timestamp | `PASS` | Nanosecond timestamp precision, timezone-naive contract; unix_time excluded; audit and schema checks pass. |
| T05 Audit and tests | `PASS` | 13 passed, 0 skipped, one third-party deprecation warning. |
| T06 Git/LFS safety | `PASS` | Raw checksums unchanged; raw LFS tracking and scoped attributes unchanged; generated Parquet files are ignored/untracked. |
| T07 GitHub verification/handoff | `BLOCKED` | Remote fetch returned `Repository not found`; no server state certified. No commit, push, merge, or PR. |

## Completed

- Made `nearest_row_count` the default splitter and pipeline policy; retained explicit `legacy` mode for reproducing the former split.
- Regenerated full-data splits, metadata, EDA outputs, reports, and config for the current policy.
- Confirmed the split hash and generated outputs match the independently saved nearest-row-count proposal artifacts.
- Reran all tests and notebook against the new artifacts.
- Backed up pre-switch reports and EDA outputs outside the repository before regeneration.

## Conditions and blockers

- `TOAN_SPRINT1_REMAINING_WORK.md` is absent from the repository; its contents were not read or audited.
- GitHub fetch returned `Repository not found`; local remote-tracking refs may be stale.
- Parquet data under `data/processed/` and `data/splits/` is local, ignored, and untracked. It is not a shared handoff artifact.
- Notebook execution logged a non-fatal Windows ZeroMQ/Proactor warning despite exit code 0.

## Overall status

`CONDITIONAL_READY`. The split and tests are ready for review locally. Downstream users need access to the regenerated artifact set (or must reproduce it from the raw inputs); remote state and the missing remaining-work document remain unresolved.
