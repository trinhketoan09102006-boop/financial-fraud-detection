# T05 — Final review and Git delivery preparation

## Review of code and contract

Reviewed `behavioral.py`, `validate_behavioral.py`, and `test_behavioral_features.py` against D01–D06. Exactly ten ordered features; `cc_num` grouping and timestamp batching make past-only histories with equal-time isolation. Queues use inclusive lower boundary; Welford moments use population standard deviation, ratio guards zero mean, novelty uses per-card sets, hour circular resultant uses 1e-12, and all split rows are processed as one history. Target is dropped from the feature computation view. Validation covers IDs, manifest coverage and allowed splits, finite amount, timezone-naive nanosecond timestamp, null categories, hash and output schema/checksums; current artifacts independently validated PASS. No correctness blocker identified for the tested dataset.

Limits requiring future review: online watermark/replay is a design contract, not an implemented service; builder validates the semantic manifest hash when configured and CLI fixes the expected split/hash/counts; generation uses uncommitted source and the base HEAD alone cannot reproduce it. The validator checks artifact metadata and hashes for the exact files, but not all possible numerical correctness failures; synthetic tests and T03 provide additional evidence. No formula or test fixture was changed during T05.

## Regression

One full run `.\.venv-clean\Scripts\python.exe -m pytest -q -rs`: **23 passed, 0 failed, 0 skipped**, 606 warnings, 40.09 s. Nine collected behavioral cases passed as part of that full run; no separate second test run was made. Existing unreviewed `tests/test_mock_data.py` contributed to the 23-pass result; the outcome on a future branch omitting that fix is not certified. T04 smoke joined 1,852,394 rows; T03 quality passed. T05 artifact validator passed with 1,037,340 / 259,335 / 555,719 rows and split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8`.

## Git and artifacts

Trung reports successful Windows PowerShell `git status`, `git lfs ls-files`, `git lfs status`, and an empty `git diff --cached --name-only`; raw file hashes match LFS OIDs. This is user-reported evidence and not independent Codex confirmation. Codex still returns `fatal: this operation must be run in a work tree` for status/check-ignore; exact sandbox cause unproven. `git ls-files --others --exclude-standard data/features/behavioral_v1` now lists only `metadata.json`, demonstrating the new narrow `.gitignore` rule excludes three untracked Parquets under active rules. No tracked-file state is inferred from that command. User reports no staged files before T05; no staging commands were executed in T05.

`docs/trung/BEHAVIORAL_V1_ARTIFACT_REFERENCE.json` records version, schema, counts, input/output checksums, null policy, generation and environment. It is a reference snapshot and does not replace runtime metadata. The runtime metadata is intentionally excluded from this proposed commit pending policy. Feature Parquets remain local and are excluded by the new rule.

All eleven files in `results/features/behavioral_v1/` exist, total 265,330 bytes; CSV headers/data are aggregate summaries or correlation matrices with no transaction IDs/card IDs, train fraud summaries use train labels only, and chart content is aggregated. T03 report statistics and summary agree; no test-label feature selection or performance claim. Images are derived from aggregate distributions. These generated evidence files are proposed for review/commit by the team.

Historical notes in T01/T02/T04 record past approval or permission state; later updates identify their superseding decisions. Runtime 140.53 s is feature generation; 79.76 s is T03 assessment; 668 MiB is an earlier artifact validation peak, not feature-generation memory. Cross-machine rebuild remains unverified. Tùng/Khoa modules were not present at T04.

## Explicit allowlist

The four source files listed first were delivered in Commit 1; Commit 2 contains the remaining 30 files plus the three reproducibility package files listed below.

- `.gitignore`
- `src/features/behavioral.py`
- `src/features/validate_behavioral.py`
- `tests/test_behavioral_features.py`
- `docs/trung/PRE_SPRINT1_ENVIRONMENT_CHECK.md`
- `docs/trung/S1_T01_FEATURE_DICTIONARY.md`
- `docs/trung/S1_T01_FEATURE_CONTRACT_AND_ARCHITECTURE.md`
- `docs/trung/S1_T01_DESIGN_AUDIT.md`
- `docs/trung/S1_T01_OPEN_SOURCE_FEATURE_REVIEW.md`
- `docs/trung/S1_T02_IMPLEMENTATION_REPORT.md`
- `docs/trung/S1_T02_TEST_REPORT.md`
- `docs/trung/S1_T02_FEATURE_OUTPUT_VALIDATION.md`
- `docs/trung/S1_T02_HANDOFF_GUIDE.md`
- `docs/trung/S1_T03_FEATURE_QUALITY_REPORT.md`
- `docs/trung/S1_T03_INTEGRATION_READINESS.md`
- `docs/trung/S1_T03_EXECUTION_LOG.md`
- `docs/trung/S1_T04_INTEGRATION_AUDIT.md`
- `docs/trung/S1_T04_REPRODUCIBILITY_GUIDE.md`
- `docs/trung/S1_T04_GIT_AND_ARTIFACT_AUDIT.md`
- `docs/trung/S1_T04_HANDOFF_READINESS.md`
- `docs/trung/BEHAVIORAL_V1_ARTIFACT_REFERENCE.json`
- `docs/trung/SPRINT1_TRUNG_FINAL_HANDOFF.md`
- `docs/trung/S1_T05_FINAL_REVIEW.md`
- `results/features/behavioral_v1/assessment_summary.json`
- `results/features/behavioral_v1/distribution_comparison.png`
- `results/features/behavioral_v1/feature_statistics.csv`
- `results/features/behavioral_v1/missing_rate.png`
- `results/features/behavioral_v1/novelty_rate.png`
- `results/features/behavioral_v1/novelty_rates.csv`
- `results/features/behavioral_v1/train_fraud_comparison.csv`
- `results/features/behavioral_v1/train_pearson.csv`
- `results/features/behavioral_v1/train_pearson_heatmap.png`
- `results/features/behavioral_v1/train_spearman.csv`
- `results/features/behavioral_v1/velocity_median.png`

- `docs/trung/t03_assess.py`
- `docs/trung/t03_reports.py`
- `docs/trung/requirements-behavioral-v1-snapshot.txt`

## Explicit exclusions

`data/raw/fraudTrain.csv`, `data/raw/fraudTest.csv`, `docs/data_manifest.json`, every `results/eda/` file, `tests/test_mock_data.py`, the three `data/features/behavioral_v1/*.parquet` files, runtime `data/features/behavioral_v1/metadata.json` pending policy, `data/processed/`, `data/splits/`, `.venv/`, `.venv-clean/`, caches, logs and temporary files. Do not stage unrelated changes or use broad staging. Check `.gitignore` diff contains only the intended rule.

## Proposed PowerShell commands — Commit 2 only

Commit 1 is complete. After approval run the following from the repository root. Review the staged names, count, content, exclusions and whitespace before a separate commit decision.

```powershell
Set-Location 'C:\Users\MSI\Desktop\financial-fraud-detection'
git status --short --branch --untracked-files=all
git diff --cached --name-only
git add -- `
  'docs/trung/PRE_SPRINT1_ENVIRONMENT_CHECK.md' `
  'docs/trung/S1_T01_FEATURE_DICTIONARY.md' `
  'docs/trung/S1_T01_FEATURE_CONTRACT_AND_ARCHITECTURE.md' `
  'docs/trung/S1_T01_DESIGN_AUDIT.md' `
  'docs/trung/S1_T01_OPEN_SOURCE_FEATURE_REVIEW.md' `
  'docs/trung/S1_T02_IMPLEMENTATION_REPORT.md' `
  'docs/trung/S1_T02_TEST_REPORT.md' `
  'docs/trung/S1_T02_FEATURE_OUTPUT_VALIDATION.md' `
  'docs/trung/S1_T02_HANDOFF_GUIDE.md' `
  'docs/trung/S1_T03_FEATURE_QUALITY_REPORT.md' `
  'docs/trung/S1_T03_INTEGRATION_READINESS.md' `
  'docs/trung/S1_T03_EXECUTION_LOG.md' `
  'docs/trung/S1_T04_INTEGRATION_AUDIT.md' `
  'docs/trung/S1_T04_REPRODUCIBILITY_GUIDE.md' `
  'docs/trung/S1_T04_GIT_AND_ARTIFACT_AUDIT.md' `
  'docs/trung/S1_T04_HANDOFF_READINESS.md' `
  'docs/trung/BEHAVIORAL_V1_ARTIFACT_REFERENCE.json' `
  'docs/trung/SPRINT1_TRUNG_FINAL_HANDOFF.md' `
  'docs/trung/S1_T05_FINAL_REVIEW.md' `
  'results/features/behavioral_v1/assessment_summary.json' `
  'results/features/behavioral_v1/distribution_comparison.png' `
  'results/features/behavioral_v1/feature_statistics.csv' `
  'results/features/behavioral_v1/missing_rate.png' `
  'results/features/behavioral_v1/novelty_rate.png' `
  'results/features/behavioral_v1/novelty_rates.csv' `
  'results/features/behavioral_v1/train_fraud_comparison.csv' `
  'results/features/behavioral_v1/train_pearson.csv' `
  'results/features/behavioral_v1/train_pearson_heatmap.png' `
  'results/features/behavioral_v1/train_spearman.csv' `
  'results/features/behavioral_v1/velocity_median.png' `
  'docs/trung/t03_assess.py' `
  'docs/trung/t03_reports.py' `
  'docs/trung/requirements-behavioral-v1-snapshot.txt'
$stagedFiles = @(git diff --cached --name-only)
$stagedFiles
"Staged file count: $($stagedFiles.Count)"  # expected 33
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git diff --cached
$stagedFiles | Where-Object { $_ -match '^(data/raw/|data/processed/|data/splits/|data/features/|results/eda/|\.venv/|\.venv-clean/)' -or $_ -in @('tests/test_mock_data.py','docs/data_manifest.json') }
```

Proposed commit message after review: `docs: add behavioral feature handoff evidence`. No command was executed for staging or commit.

## Remaining decisions / readiness

Trung approves exact allowlist and commits; Toàn reviews fixture; team decides runtime metadata and generated evidence policy, Git/LFS handling, online history/late events, real Tùng/Khoa integration and cross-machine reproduction. **TECHNICAL_HANDOFF_READY: YES locally, conditional. READY_FOR_MANUAL_STAGING: YES after review. READY_FOR_COMMIT: NO until approval and staged diff review.**

## Post-source-commit update — current status

Commit 1 COMPLETE locally: `af71e9d3a07180e92de7bbf19f72a37eb0d91fad`, `feat: add leakage-aware behavioral features`, containing exactly `.gitignore`, `src/features/behavioral.py`, `src/features/validate_behavioral.py`, `tests/test_behavioral_features.py`. HEAD and commit contents were read directly in this session; current working-tree source blobs match the commit. According to Trung, feature-only tests were 9/9 PASS in 2.38 s with one pandas warning, whitespace check PASS, three Parquets ignored, no raw CSV or Toàn changes committed; Git status/LFS worked in normal Windows PowerShell. Codex `git status` still fails, so current staging state cannot be independently certified here. No push is reported.

The original generation used uncommitted feature source on base HEAD `0161186bdc1ac0eb0d88a7638dad67d1b9fbf029`. The new commit is a source delivery identifier; artifacts were not regenerated from it. Trung reports only trailing blank lines were removed from the two Python source files before committing. The reference JSON now records current source/test SHA-256 and UTC-normalized generation timestamp without changing artifact hashes or runtime metadata.

Current `.venv-clean` passed `pip check`. The two preserved proposed freeze files each contain 121 entries and match the current `pip freeze` as a set, SHA-256 `403c069d2ddd822a4e1dbba23bbd12f1323471ca6a0f1a0ed078e590df3926d6`. They are local workspace snapshots, not a tested portable lock. `t03_assess.py` and `t03_reports.py` exist in the Codex workspace, outside repository and commit 1. Propose a separate review and delivery decision for them and the dependency snapshot; they are not added to Commit 2. Full T03 reproduction on another machine remains unverified.

Prior full suite 23 PASS depended on Toàn's unreviewed fixture fix. Tùng/Khoa modules were absent at T04. Online history availability and late-arrival behavior still need team approval. The historical Commit 2 allowlist contained 19 documentation/reference files and 11 aggregate evidence files; the later packaging update adds three reviewed reproducibility files; no source file, runtime metadata, raw data, split or Parquet should be staged for this commit. The historical source commit command above is already completed. Commit 2 remains pending Trung's approval and a fresh staged-diff review.

## Reproducibility packaging update

Commit 2 now proposes 33 explicit files: the previous 30 plus `docs/trung/t03_assess.py`, `docs/trung/t03_reports.py` and `docs/trung/requirements-behavioral-v1-snapshot.txt`. The earlier proposal to deliver workspace copies separately is superseded. The repository-root `scripts/` parent could not be created under the granted sandbox permissions, so the reviewed scripts are alongside the handoff docs. Both scripts derive repository root from location, have `--help`, refuse accidental overwrites by default and cannot target `data/` for output. The report template is restricted to the original T03 artifact hashes and expected table shapes; aggregate table provenance still needs verification. Syntax, imports, snapshot pins, help, and rendering existing aggregate results to a separate workspace directory passed; no full assessment was rerun. Snapshot SHA-256 `403c069d2ddd822a4e1dbba23bbd12f1323471ca6a0f1a0ed078e590df3926d6`, 121 package pins, is a snapshot of Python 3.14.4 / pandas 3.1.1 / PyArrow 26.0.1, not an official team lock; cross-machine rebuild remains unverified.
