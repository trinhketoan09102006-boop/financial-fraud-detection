# Pre-Sprint 1 environment check — 2026-11-24

Repository: `C:\Users\MSI\Desktop\financial-fraud-detection`
Branch: `trung/feature-engineering-s1`
HEAD: `0161186bdc1ac0eb0d88a7638dad67d1b9fbf029`

## A. Desktop cleanup

All direct Desktop folders related to this task were inventoried. Four verified folders were sent to Windows Recycle Bin, one at a time using exact paths. Before recycling, all 78 files were copied to `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\desktop_preserved`; relative paths and SHA-256 hashes matched the originals.

| Recycled folder | Desktop footprint |
|---|---:|
| `fraud_final_fix_backup` | 1,218,364 bytes |
| `fraud_final_fix_report` | 9,045 bytes |
| `fraud_fresh_setup_report` | 5,275 bytes |
| `financial-fraud-detection-clone-incomplete` | 519,195 bytes |

Desktop footprint removed: **1,751,879 bytes (1.67 MiB)**. Actual disk space is not freed until Recycle Bin is emptied. The six small report folders listed in an earlier cleanup plan were already absent at this inventory.

Preserved on Desktop:

- `financial-fraud-detection`: main repository, untouched by cleanup.
- `financial-fraud-detection-old`: same HEAD but contains an untracked `docs/TOAN_SPRINT1_REMAINING_WORK.md` and ignored processed/split Parquet files with hashes different from the main repository. The unique document was also copied into `desktop_preserved`; original remains intact.
- `fraud_data_artifact_backup`: seven files, 255,356,692 bytes, including Parquet files with hashes different from the current artifacts. Retained as a distinct recovery point.

The prior test fix remains in the main repository and a copy of its earlier state remains in the preserved backup. Existing data contract, handoff, dependency lock proposal, logs, and pre-run artifacts remain accessible. No unrelated Desktop folders were touched.

## B. Environment validation

| Check | Result |
|---|---|
| Interpreter | `.venv-clean\Scripts\python.exe`, Python 3.14.4 |
| pandas / PyArrow / pytest | 3.1.1 / 26.0.1 / 9.2.0 |
| Isolated venv | `include-system-site-packages = false` |
| `python -m pip check` | PASS: `No broken requirements found.` |

No dependencies were installed or changed during this check.

## C. Pipeline and data validation

Command, run once from the main repository: `.\.venv-clean\Scripts\python.exe -m src.data.pipeline --stage all --force --cutoff-policy nearest_row_count`. CLI help confirmed the flags. Existing output files were inventoried and processed/split Parquet, metadata, manifest, schema, config, and test fixture were backed up before the run. Full log: `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\pre_sprint1_backup\pipeline.log`.

**Exit 0; 184.21 seconds.** Audit found zero blockers. Preprocess produced **1,852,394 rows and 25 columns**. Arrow field names and types matched **25/25** contract fields. Raw train/test SHA-256 remained respectively `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d` and `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`.

| Output | SHA-256 after run |
|---|---|
| Processed transactions | `111d9d7e3d8c959728aafd3787701595285acbdf9c807433f5b718dcef637626` |
| Split manifest | `86d8a6e44e01464a82540ba07ff0a1da8e1a44045c61a94436351f36f987fe96` |
| Train | `9c816f595a5e0b866a14a3a315c0cee11c68f5c70df63a956f3e22490ebc13ce` |
| Validation | `fea4d6277c283d3b82b19fb26604c2c1b4444c6ac165e22a148918c842cd5d8f` |
| Test | `2cc7727fd2f00f57212d58fc5b12dc912613e0857a9a286cc417c45c0fefb764` |
| Split metadata | `9221effe5a7d676e4b76fd1ffe32f63822ed1f6f7d60190c8dceed3a623af3e9` |

Output byte hashes differ from the pre-run artifacts, consistent with rewriting under the new environment; semantic checks passed. Full before/after hashes and validation output are saved under `pre_sprint1_backup`.

IDs: unique and non-null; raw-to-processed `trans_num`, `cc_num`, `is_fraud`, and source dataset all matched one-to-one. Label counts were unchanged: normal 1,842,743; fraud 9,651. Processed/manifest join is one-to-one. No timestamp appears in more than one split, time ranges are strictly chronological, and test IDs exactly match raw `fraudTest` IDs.

| Split | Rows |
|---|---:|
| Train | 1,037,340 |
| Validation | 259,335 |
| Test | 555,719 |

Policy: `nearest_row_count`; semantic split hash in config and metadata: `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

## D. Test results

Command: `.\.venv-clean\Scripts\python.exe -m pytest -q -rs`. **Exit 0; 14 passed, 0 failed, 0 skipped**, including full-data integration test; elapsed 73.40 seconds (pytest reported 70.95 seconds). There were **604 `Pandas4Warning`** deprecation warnings for `dayofweek` in preprocessing and mock generation. Full log: `C:\Users\MSI\Documents\Codex\2026-11-22\files-pasted-by-the-user-task\pre_sprint1_backup\pytest.log`.

## E. Git status

Branch and HEAD remained unchanged. Modified tracked files: `data/raw/fraudTrain.csv`, `data/raw/fraudTest.csv`, `docs/data_manifest.json`, ten `results/eda/*.png`, `results/eda/numeric_summary.csv`, and `tests/test_mock_data.py`. New untracked file: this report. The raw CSV byte checksums are unchanged; the existing Git LFS status/filter issue makes Git mark them modified. The test fix remains uncommitted and its checksum stayed unchanged across this run. `src/` and `configs/` have no Git diff; split/schema config hashes are unchanged.

Do not accidentally stage or commit the two raw CSV paths, generated manifest/EDA output, or the unreviewed test fixture. No files were staged. No commit, push, merge, rebase, reset, clean, or Git LFS configuration change was made.

## F. Final readiness

| Gate | Status |
|---|---|
| DATA_READY | YES |
| SPLIT_READY | YES |
| SCHEMA_READY | YES |
| ENVIRONMENT_READY | YES |
| TESTS_READY | YES |
| GIT_READY | CONDITIONAL: dirty working tree and unresolved LFS status issue |
| TRUNG_SPRINT1_READY | YES, conditional |

**Decision: CONDITIONAL GO.** Trung can begin Sprint 1 Feature Engineering against the verified local data and environment. Toàn should review the existing uncommitted test fixture fix. The group lead or repository owner should decide how to reconcile the Git LFS status and generated documentation/EDA changes before any commit or handoff; preserve the distinct old Parquet backup until its retention need is decided. Deprecation warnings are non-blocking maintenance work.
