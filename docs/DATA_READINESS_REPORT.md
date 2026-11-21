# Data readiness report

## Decision summary

- **DATA_PIPELINE_READINESS: PASS** for local development and model input generation.
- **MODEL_INPUT_READINESS: PASS** for the validated temporal splits and declared baseline feature contract.
- **TEAM_HANDOFF_READINESS: CONDITIONAL** because the raw files remain tracked in Git LFS and the owner has not approved how to remove them from the current repository tip.
- **GIT_SAFETY_READINESS: BLOCKER** for a clean handoff or merge until the team chooses a history-preserving untracking plan or an explicitly coordinated history rewrite.
- **OVERALL: NO-GO for merge/team Git handoff; data can be used locally.**

## Data checks

| Criterion | Status | Evidence |
|---|---|---|
| Full source read | PASS | Both files were audited in full. |
| Source row counts | PASS | Train 1,296,675; test 555,719; total 1,852,394. |
| Labels | PASS | Train 7,506 fraud; test 2,145 fraud; all labels are 0/1. |
| Schema / IDs | PASS | Same 23 columns; no duplicate rows, duplicate/missing `trans_num`, or cross-file transaction ID overlap. |
| Timestamp parsing | PASS | `trans_date_trans_time` parses for all rows; `fraudTest` begins after `fraudTrain`. Train has one source-order decrease, handled by sorting on timestamp. |
| `unix_time` root cause | WARNING, resolved | It is epoch seconds; interpreting as UTC and adding seven calendar years reconstructs the text timestamp exactly for all 1,852,394 records. It is excluded from normalized/model data. Raw CSVs remain unchanged. Code: `UNIX_TIME_STALE_BY_7_CALENDAR_YEARS`. |
| Missing / numeric / coordinate / DOB checks | PASS | No missing values, blank strings, invalid labels/timestamps, invalid amounts, invalid coordinates, or future DOBs observed. |
| Card identifier lengths | WARNING | 6,111 train and 2,708 test IDs are 11-digit strings. Preserved exactly as strings for history grouping; never passed to a model. |
| Processed table | PASS | 1,852,394 rows, 25 columns, unique `trans_num`, no `unix_time`, names, surname, or street fields. |
| Temporal split | PASS | Train 1,037,339; validation 259,336; test 555,719; strict time order, no equal-timestamp group crosses a boundary, and transaction IDs are pairwise disjoint. |
| Reproducibility | PASS | Split hash is unchanged from the earlier provisional artifact and recomputes from the regenerated manifest. |
| EDA | PASS | Ten charts and aggregate outputs rerun on training split only. |
| Contract / mock / tests | PASS | YAML contract validated; 300 synthetic rows span 1h/24h/7d windows; 8 pytest tests pass. |
| Raw checksums | PASS | Both raw SHA-256 values match the full audit manifest after the rerun. |

## Git LFS status

The two CSVs were introduced in commit `ff8baf41502b39fc8fa477f259e50ae0b8f84de6` (`Update data thô`). The commit is at local `toan` and `origin/toan`; `origin/main` does not contain it. `.gitattributes` currently applies Git LFS to every `*.csv`. `.gitignore` matches the raw files only for future untracked files; it does not untrack them. No CSV or Git history/index operation was changed in this task.

### Option A — stop tracking in a future commit, preserve history (recommended)

Remove the raw files from the current index in a new commit, keep the local copies, and narrow the LFS attribute rule to raw inputs only. This avoids rewriting commit IDs and is the least disruptive path. The old `toan` commit and LFS objects remain reachable, so this does **not** purge history or reduce existing LFS storage. When collaborators pull the deletion commit, Git may remove their checked-out raw paths; they should back up or relocate the local CSVs first.

### Option B — rewrite Git/LFS history

Coordinate a `git lfs migrate`/history cleanup, force-update remote branches, and ensure old LFS objects are eventually pruned by the hosting service. This can remove the old tracked objects from reachable history, but changes commit IDs, disrupts open clones/branches, requires every collaborator to coordinate/reclone or reset, and can affect other work on shared branches. This requires an explicit team-approved maintenance window and is not performed here.

## Required before Git handoff

1. Choose Option A or B with the team.
2. For Option A, confirm collaborators have backed up the local raw CSVs before pulling a commit that removes them from the repository tip.
3. Apply and review the Git LFS remediation in a separate approved change; no Git history, staging, commit, push, or merge operations were performed here.
