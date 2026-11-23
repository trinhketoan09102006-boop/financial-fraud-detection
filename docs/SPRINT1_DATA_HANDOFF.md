# Sprint 1 – Data handoff

## 1. Executive summary

The data pipeline and model inputs now **PASS** for local team development. Full-data checks establish `trans_date_trans_time` as canonical and show that `unix_time` is exactly seven calendar years stale; it has been excluded from normalized data. The Git handoff remains **BLOCKED** because both raw files are already LFS-tracked in the published `toan` branch. No model training, sampling, SMOTE, or validation/test feature exploration was performed.

## 2. Raw data inventory

`data/raw/fraudTrain.csv` (351,238,196 bytes) and `data/raw/fraudTest.csv` (150,354,339 bytes) were read in full. Their SHA-256 values are stored in `docs/data_manifest.json`. They remain byte-for-byte unchanged after audit.

## 3. Data audit

Observed counts match the reference: train 1,296,675 (1,289,169 normal / 7,506 fraud), test 555,719 (553,574 normal / 2,145 fraud). Files share the same 23 columns. There are no missing values, duplicate complete rows, duplicate/missing transaction IDs, cross-file transaction-ID overlaps, invalid labels, invalid parsed text timestamps, negative/zero/non-finite amounts, invalid coordinates, or future DOB values. Train source order has one timestamp decrease; temporal processing sorts by timestamp. A warning records 6,111 train and 2,708 test card identifiers with 11 digits; they are preserved as strings, with no actual card values exposed.

**Resolved warning:** `unix_time` is epoch seconds. Interpreting it as UTC and adding seven calendar years reconstructs `trans_date_trans_time` exactly across all 1,852,394 records. `unix_time` is chronological in both files (zero decreases); text timestamp train has one original-order decrease. Audit code: `UNIX_TIME_STALE_BY_7_CALENDAR_YEARS`. See `docs/data_audit.md` and `docs/data_manifest.json`.

## 4. Preprocessing decision

The full normalized Parquet was regenerated after verifying the timestamp root cause. It preserves all 1,852,394 rows, parses `timestamp` from `trans_date_trans_time`, preserves `cc_num` and `zip` as strings, removes `unix_time`, the redundant index, `first`, `last`, and `street`, and adds transaction-local calendar, age, and straight-line distance fields. Raw files and their hashes are unchanged.

## 5. Proposed schema

The validated normalized schema is in `configs/data_schema.yaml`; the data contract is in `docs/DATA_CONTRACT.md`. `trans_num` is the unique join key, `cc_num` is a history-grouping identifier and is not a model input, `is_fraud` is the target, and `source_dataset` is metadata. `unix_time` appears only as an excluded source field and audit diagnostic.

## 6. Temporal split

The current regenerated time split uses `nearest_row_count` and canonical `timestamp`: train 1,037,340 rows, validation 259,335, test 555,719. Cutoff: `2020-03-06T07:16:43`. All equal timestamps stayed together; `max(train) < min(validation) < min(test)`. Transaction IDs are pairwise disjoint. Current split hash: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. The former baseline hash `70886bb39220a732c02d0fd1fe2568bdbcaee96d9e3434c73bd9477c02ebb255` is retained only as historical evidence.

## 7. EDA

EDA reran only on train (1,037,340 rows, 5,968 fraud; fraud rate 0.5753%). Ten PNG figures and aggregate statistics are in `results/eda/`; detailed notes are in `docs/eda_report.md`. No direct names, street addresses, or card numbers appear in the EDA outputs.

## 8. Data contract

Contract files: `configs/data_schema.yaml`, `configs/base_features.yaml`, `docs/DATA_CONTRACT.md`. The current baseline candidates are `amt`, calendar fields, `age_at_transaction`, `merchant_distance_km`, `merchant`, and `category`. No history-based features are implemented here.

## 9. Leakage prevention

The split is temporal, not random. For future behavioral features, only same-card transactions strictly earlier than the event may be used; all events at an equal timestamp form a batch. Do not use target labels in history or fit transforms on validation/test. Prior observed train history can be used for later validation/test events.

## 10. Mock dataset

`data/samples/mock_transactions.csv` and `mock_split_manifest.csv` contain 300 synthetic rows across train/validation/test. Each split contains both labels and includes tied timestamps, unseen cards, new merchant/category values, a large amount, and nullable fields. The README clearly marks the fixture synthetic and unsuitable for model performance claims.

## 11. Test results

`python -m pytest -q -rs` after regenerating the `nearest_row_count` artifacts: **13 passed, 0 skipped**, with one third-party pytest deprecation warning. Python compilation and `pip check` pass. Tests cover audit aggregate privacy and stop conditions, canonical timestamp normalization, temporal splitting, feature exclusions, mock data, and full-data integration including source checksums, stale-time reconstruction, row preservation, split boundaries and hash.

## 12–15. Guidance for Trung, Tú, Tùng, and Khoa

- **Trung:** consume normalized transactions and the split manifest. Return one feature row per `trans_num`; histories must be strictly past-only and equal-time batched.
- **Tú:** baseline inputs are ready locally. Join by `trans_num`; keep IDs, target, and source metadata out of `X`.
- **Tùng:** do not resample validation/test. Sampling or class weights may apply to train only.
- **Khoa:** use `trans_num, model_id, score, split`; attach threshold, seed, feature set, strategy, commit hash, and split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

## 16. Limitations and decisions needed

Sparkov is simulated data. Currency and timezone are unspecified. Card-format warnings remain for 11-digit identifiers: 6,111 train and 2,708 test; they are preserved as strings and excluded from model features. The two raw CSVs are already LFS-tracked in `toan` and `origin/toan`; `.gitignore` does not untrack them. No index/history change was made. The split policy switch was requested by Toan on 2026-11-23; `nearest_row_count` is the current policy in this worktree.

The data files were added by commit `ff8baf41502b39fc8fa477f259e50ae0b8f84de6` (`Update data thô`), which is at local `toan` and `origin/toan`; `origin/main` does not contain it. `.gitattributes` applies LFS only to `data/raw/*.csv`; mock and EDA CSVs are outside that rule. Option A (untrack in a later commit) preserves history but leaves the old LFS objects reachable and can remove local raw paths when collaborators pull. Option B (rewrite) can purge reachable history but requires coordinated force-push and clone repair. Readiness options and impact are detailed in `docs/DATA_READINESS_REPORT.md`.

## 17. Remaining work

Choose a team-approved Git LFS remediation (history-preserving untrack in a future commit, or coordinated history rewrite if historical purging is required). Coordinate local CSV backups before a removal commit. Do not commit/merge this handoff until that Git decision is resolved.
