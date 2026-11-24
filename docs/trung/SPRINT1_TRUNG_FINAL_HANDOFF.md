# Sprint 1 — Trung final handoff

## Executive summary

T01–T03 complete; T04 technical integration smoke passed, with Git and deployment reviews pending. Behavioral V1 provides ten strictly historical card features for 1,852,394 transactions. Commit 1 is complete locally at `af71e9d3a07180e92de7bbf19f72a37eb0d91fad` (`feat: add leakage-aware behavioral features`); it has not been pushed, according to Trung. Commit 2 remains for review and approval. Technical local handoff is ready with conditions.

## Features

For card c at time t let H contain all observed same-card transactions with timestamp < t. Same-card equal timestamps are computed as a batch before any member updates state.

| Feature | Definition |
|---|---|
| `txn_count_1h` | count in `[t-1h,t)` |
| `txn_count_24h` | count in `[t-24h,t)` |
| `txn_count_7d` | count in `[t-7d,t)` |
| `hist_amt_mean` | mean historical amount over H |
| `hist_amt_std` | population std over H (`ddof=0`) |
| `amt_ratio` | current amount divided by finite nonzero historical mean |
| `txn_recency` | seconds since latest earlier card transaction |
| `is_new_merchant` | current valid merchant not in historical set |
| `is_new_category` | current valid category not in historical set |
| `hour_deviation` | shortest 24-hour circular distance from history circular mean; resultant epsilon 1e-12 |

## Architecture and checks

Normalized transactions + split manifest → sorted per-card timestamp groups → past-only rolling queues, running moments and seen sets → ten keyed outputs → split Parquet and metadata → independent validation. Labels never enter feature state. Train 1,037,340, validation 259,335, test 555,719. Artifact schema/hash/one-to-one coverage and baseline join passed. T03 invariants pass, 44 real tied groups verified and 999 cold starts explained. T05 full regression: 23 passed, 0 failed, 0 skipped, 606 warnings, 40.09 s in current worktree; includes Toàn's unreviewed fixture fix. Nine behavioral cases were collected in that full suite. Feature generation took 140.53 s; T03 assessment took 79.76 s; 668 MiB refers only to a prior validation peak, not generation peak.

## Use

After reviewed source is delivered and authorized upstream data prepared, from repository root:

```powershell
py -3.14 -m venv .venv-clean
.\.venv-clean\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-clean\Scripts\python.exe -m pip check
# If upstream processed data and splits are absent, obtain authorized raw data first.
.\.venv-clean\Scripts\python.exe -m src.data.pipeline --stage all --cutoff-policy nearest_row_count
# Only when feature output destination is absent/empty:
.\.venv-clean\Scripts\python.exe -m src.features.behavioral
.\.venv-clean\Scripts\python.exe -m src.features.validate_behavioral
.\.venv-clean\Scripts\python.exe -m pytest -q -rs
```

The feature source has been committed locally; `requirements.txt` is not pinned; see `S1_T04_REPRODUCIBILITY_GUIDE.md` for a join example and limitations. Check split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`. Join each matching split by `trans_num` one-to-one; X may contain the nine baseline fields plus ten behavioral fields in contract order, y comes separately, and IDs/metadata/labels must be excluded from X. Fit preprocessing only on train; preserve NaN for undefined history and do not replace it with zero blindly. Compute features before sampling; only train may be resampled.

Historical state crosses split boundaries only for already observed non-target transactions. Merchant novelty is 42.64% train, 14.16% validation and 9.04% test, a descriptive difference and not a model performance claim.

## Pending decisions

- Toàn review and delivery of the existing test fixture fix; the remote branch without it is not certified 23/23.
- Team policy for runtime metadata and approved access-controlled artifact delivery; Parquet is ignored locally.
- Online observed-history availability, ordering, watermark and late event reject/replay behavior.
- Actual integration with Tùng and Khoa, whose modules were absent at T04, and cross-machine reproducibility.
- Git staging/commit after Trung reviews the exact allowlist in `S1_T05_FINAL_REVIEW.md`.

Possible Sprint 2 candidates only: `amt_zscore`, `amt_sum_24h`; neither is implemented here.

## Source delivery update

Trung reports feature-only tests **9 passed, 0 failed, 2.38 seconds**, one pandas warning and whitespace check PASS before commit; Git status and LFS worked in normal Windows PowerShell. Source commit contains `.gitignore`, the two feature modules, and the feature test only. The full suite result above was measured before this commit on a working tree containing Toàn's unreviewed fixture; it is not proof of 23/23 for the source commit alone. Source delivery commit is not proof of the source bytes used for feature generation; artifacts were not rebuilt. No push is reported.

A 121-package proposed freeze in the Codex workspace matched current `pip freeze` as a set, and `pip check` passed; it has not been proven as a portable or cross-machine rebuild lock. T03 assessment scripts `t03_assess.py` and `t03_reports.py` exist in the workspace, not in the source commit; review and deliver separately if reproducibility is required. Reproduction on another machine remains unverified. Online observed history and late-event policy remain pending, and Tùng/Khoa modules were absent at T04.

## Reproducibility packaging update

The T03 scripts are included for review as `docs/trung/t03_assess.py` and `docs/trung/t03_reports.py`; this location is used because the sandbox could not create the proposed root `scripts/` directory. `docs/trung/requirements-behavioral-v1-snapshot.txt` preserves the 121-package environment snapshot (Python 3.14.4, pandas 3.1.1, PyArrow 26.0.1); it is not an official team lock. Commands, inputs, safe output destinations and overwrite behavior are documented in `S1_T04_REPRODUCIBILITY_GUIDE.md`. The previous note that these files exist only in the workspace is historical. Packaging checks did not rerun full T03 or establish reproducibility on another machine.
