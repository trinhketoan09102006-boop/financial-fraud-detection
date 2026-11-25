# T04 — Git and artifact audit

## Diagnostics

CWD/top-level `C:\Users\MSI\Desktop\financial-fraud-detection`; Git `C:\Program Files\Git\cmd\git.exe`, 2.51.0.windows.1. `rev-parse --is-inside-work-tree` true; bare false, `core.bare=false`, no local `core.worktree`; `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` unset. `.git` is a hidden directory. `git worktree list` returns this checkout at branch `trung/feature-engineering-s1`, HEAD `0161186bdc1ac0eb0d88a7638dad67d1b9fbf029`. Nevertheless `git status --short --branch` and `git check-ignore` return **`fatal: this operation must be run in a work tree`**, including with `GIT_OPTIONAL_LOCKS=0` and fsmonitor disabled. Cause remains unproven; do not describe worktree as clean. No persistent config was changed. `git ls-files --others --exclude-standard` did work and enumerated the feature files below; tracked modifications remain incompletely inventoried.

Read-only commands for Trung in a normal PowerShell terminal:

```powershell
Set-Location 'C:\Users\MSI\Desktop\financial-fraud-detection'
git status --short --branch --untracked-files=all
git diff --name-only
git diff --cached --name-only
git check-ignore -v data/features/behavioral_v1/train.parquet
git lfs ls-files -l
```

Avoid sharing unredacted `git config --list` or `git lfs env`: they may expose authentication or endpoint data. Git LFS 3.7.0 points to this working directory and `.git/lfs/objects`; `.gitattributes` tracks `data/raw/*.csv` with required LFS filter. Index pointers and current raw SHA-256 match: train `fd7139200dbfcbed0b6742bbe05a4f1abce532c4fef20918228a651647a3e75d`; test `12d553ab19440c752d2531ee1af44bb64f12cc3d3839f1649f19e81c230545f0`. This establishes content match, not a clean Git/LFS status. No LFS setting was changed.

## Change inventory

- GROUP A Trung source/docs: `src/features/behavioral.py`, `src/features/validate_behavioral.py`, `tests/test_behavioral_features.py`, T01–T04 docs under `docs/trung/`. These source/test/docs were visible to `git ls-files --others --exclude-standard` before creation of T04 docs, so untracked then. Assessment/reproduction scripts `t03_assess.py`, `t03_reports.py`, `t04_smoke.py` are in the Codex workspace, not in the repo or clone; decide whether to review and include them later.
- GROUP B Toàn/DE: pre-existing `tests/test_mock_data.py` fixture fix needs Toàn review; pre-existing `docs/data_manifest.json`, `results/eda/01_class_distribution.png` through `10_correlation_heatmap.png`, and `results/eda/numeric_summary.csv` were previously reported modified. Current tracked diff cannot be certified due to status error.
- GROUP C generated: `data/features/behavioral_v1/{train,validation,test}.parquet`, `metadata.json`, and `results/features/behavioral_v1/` tables, charts and summary. All were listed by `git ls-files --others --exclude-standard`; hence **not ignored under the active Git ignore rules** at this check. The four feature files are 54,866,423, 14,602,636, 29,803,109 and 6,868 bytes respectively.
- GROUP D raw: tracked `data/raw/fraudTrain.csv`, `data/raw/fraudTest.csv` with LFS pointers; prior status showed modified but current status unavailable.
- GROUP E unknown: any other tracked changes not visible without a working status/diff; cannot assert none.

## Proposed policy for approval

Store reviewed source, tests, configs, and docs in Git. Keep feature Parquet out of Git by default; deliver metadata/checksums and exact source/version via agreed access-controlled channel. Generated tables/plots need group decision. Proposed `.gitignore` change, **not applied**:

```diff
+ # Generated behavioral feature datasets (metadata handoff separately)
+ /data/features/behavioral_v1/*.parquet
```

If metadata should also stay out of Git, explicitly decide and add a separate rule; it currently records a dirty/unknown status and versions. Avoid staging raw files, Parquet, Toàn fixture, or EDA until each owner reviews. Never use `git add .`. Proposed commits after review: (1) feature source/tests, (2) T01–T04 docs and chosen reproducibility evidence, (3) independently approved artifact-ignore policy. No staging or commit done.

## T05 update — later evidence

Trung reports that in a normal Windows PowerShell session `git status --short`, `git lfs ls-files`, and `git lfs status` succeeded, the staged-name list was empty, and both LFS OIDs matched local file hashes. This is user-supplied evidence; it was not independently reproduced in the Codex sandbox, where `git status` still reports `fatal: this operation must be run in a work tree`. The exact sandbox cause remains undetermined. The narrow `/data/features/behavioral_v1/*.parquet` rule was subsequently added to `.gitignore`; current `git ls-files --others --exclude-standard data/features/behavioral_v1` lists only runtime `metadata.json`. The previous T04 statement that all three Parquet files were unignored describes the earlier check. Toàn fixture review, cross-machine reproducibility, actual Tùng/Khoa integration and deployment policy remain pending.
