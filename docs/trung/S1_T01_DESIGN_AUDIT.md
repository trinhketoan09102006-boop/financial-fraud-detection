# T01 — Design audit and decision log

> **APPROVED_FOR_T02:** Trung đã phê duyệt D01–D06 ngày 24/11/2026 trong yêu cầu S1-T02. Các dòng đề xuất hoặc chờ quyết định bên dưới là lịch sử T01; quyết định được duyệt trong yêu cầu T02 có hiệu lực.

**Date:** 2026-11-24. **Owner:** Trung. **Scope:** read-only repository review plus three T01 Markdown design files. No feature implementation or artifact generation.

## Repository and environment

- Repository: `C:\Users\MSI\Desktop\financial-fraud-detection`.
- Branch from `.git/HEAD` and `git symbolic-ref`: `trung/feature-engineering-s1`.
- HEAD from `git rev-parse`: `0161186bdc1ac0eb0d88a7638dad67d1b9fbf029`.
- Existing `.venv-clean` verification in `docs/trung/PRE_SPRINT1_ENVIRONMENT_CHECK.md`: Python 3.14.4, pandas 3.1.1, PyArrow 26.0.1, pytest 9.2.0; pipeline exit 0, 14 tests passed. T01 did not rerun the pipeline or tests.
- `src/features/` contains only `.gitkeep`; there is no existing public feature API to preserve.
- `git status`/`git diff` returned `fatal: this operation must be run in a work tree` during this read-only T01 session, although `git rev-parse --is-inside-work-tree` returned true and branch/HEAD could be read. This is an environment/tooling limit of the current inspection, not evidence of a new repository change. The preceding environment-check report records the pre-existing modified raw CSV status, unreviewed `tests/test_mock_data.py`, generated manifest/EDA changes, and its own untracked report. T01 did not alter or stage these files. Recheck status in a normal Git environment before any handoff/commit.

## Evidence reviewed

- `docs/DATA_CONTRACT.md`, `docs/SPRINT1_DATA_HANDOFF.md`, `docs/DATA_READINESS_REPORT.md`, `docs/sprint1_completion/07_TRUNG_FEATURE_ENGINEERING_HANDOFF.md`, `docs/sprint1_completion/08_PENDING_GROUP_DECISIONS.md`, `docs/trung/PRE_SPRINT1_ENVIRONMENT_CHECK.md`, `README.md`.
- `docs/data_manifest.json`; `configs/data_schema.yaml`, `configs/base_features.yaml`, `configs/split.yaml`; `data/splits/split_metadata.json`.
- `src/data/audit.py`, `preprocess.py`, `split.py`, `pipeline.py`, `generate_mock.py`, `eda.py`; `src/features/` listing.
- `tests/test_data_audit.py`, `test_data_contract.py`, `test_data_integration.py`, `test_data_preprocessing.py`, `test_data_split.py`, `test_mock_data.py`; related Sprint 1 completion/split reports.

## Verified contract facts

| Fact | Evidence | T01 implication |
|---|---|---|
| Unique transaction key `trans_num`, string | schema, data contract, integration test | output one row per key and join one-to-one |
| Historical card key `cc_num`, string, not model feature | schema, preprocessing, data contract | per-card state; retain leading digits/format, exclude from `X` |
| Canonical `timestamp` is timezone-naive `timestamp[ns]` from `trans_date_trans_time` | schema, preprocessing, contract, tests | strict event-time comparison; no invented UTC conversion |
| `amt` float64; `merchant`, `category` Arrow string | schema, preprocessing, tests | running amount moments and string seen sets |
| `is_fraud` target, `source_dataset` metadata | schema, contract, baseline config | neither enters feature state or `X` |
| Source `unix_time` is seven calendar years stale and excluded | data manifest, contract, integration test | do not use for event time or behavioral hour |
| Train/validation split from `fraudTrain`; test from later `fraudTest` | `src/data/split.py`, handoff, metadata | process full chronological stream, then partition by manifest |
| `nearest_row_count`, split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8` | split config, metadata, test | reject mismatched feature/model artifacts |
| Train 1,037,340; validation 259,335; test 555,719 | metadata, integration test | output coverage checks |
| Past history requires same card and timestamp strictly less than anchor; tied timestamps batched | data contract, handoff | state commit only after whole same-time group |
| Prior train history may be used for validation/test | data contract | do not reset state at train boundary |
| Baseline config has transaction-local fields only | `configs/base_features.yaml` | behavioral set must be versioned separately, not silently added to baseline |

## Compatibility and discrepancies

The ten proposed behavioral features comply with the upstream key, time, type, split, and leakage rules when built from the normalized table. No Data Engineering code change is required for the design. The source schema marks `merchant` and `category` non-null and the current audit reports zero missing values; T01 nevertheless proposes NaN novelty outputs for future invalid/null values. Such null input violates today's schema and should be rejected by the strict full-data builder; the nullable novelty behavior applies to a consciously relaxed future contract or targeted robustness fixture. This precedence must be clear in T02.

The Sprint 1 handoff document lists processed/split **byte** SHA-256 values from an earlier environment. The latest `.venv-clean` rebuild rewrote Parquet bytes and recorded new checksums in `docs/trung/PRE_SPRINT1_ENVIRONMENT_CHECK.md`. The semantic split hash, row counts, keys, and schema still match. This is a documentation freshness discrepancy, not a split-policy conflict; downstream metadata must use current file checksums.

`configs/base_features.yaml` says `allowed_history: None` for `baseline_v1`; `docs/DATA_CONTRACT.md` assigns behavioral history to Trung under `src/features/`. These scopes are compatible. The old handoff's Python 3.13/pandas 2.2/PyArrow 22 environment differs from the active `.venv-clean` versions; it is historical validation, not the current runtime.

No explicit existing document settles whether *all* observed validation events may update state before later validation/test inference; the data contract explicitly mentions observed past train events. The proposed cross-split policy is consistent with strict past-only processing but needs deployment agreement. No source timezone or currency is declared; `hour_deviation` uses source-local clock values without assigning a timezone, and amount features use unnamed source amount units. Model interpretation must retain those limits.

## Decisions requested from Trung/team

| ID | Decision and proposal | Why approval matters |
|---|---|---|
| D01 | Approve observed-history updates across train -> validation -> test, including earlier validation rows, subject to real inference availability. | Determines whether later evaluation rows can use earlier validation non-target transactions; affects online parity and outputs. |
| D02 | Approve F10 circular mean of fractional hour, undefined when resultant length `<=1e-12*n`, with NaN cold start. | Different mean/epsilon choices change values, especially midnight and opposite-hour history. |
| D03 | Approve F08/F09 missing policy: current null -> NaN, historical null ignored; strict current schema rejects null in production until schema is intentionally relaxed. | Prevents missing from being misread as a new merchant/category. |
| D04 | Approve F06 `amt / hist_amt_mean` only for finite, nonzero mean, with NaN otherwise; F05 uses population `ddof=0`. | Ensures consistent model preprocessing and edge behavior. |
| D05 | Approve fixed output order/types, separate `data/features/behavioral_v1/` path and metadata sidecar; `trans_num` only as join key, split stored as partition/metadata rather than predictor. | Tú/Tùng/Khoa need a stable input and reproducibility contract. |
| D06 | Confirm source timezone/currency conventions if known. Until then keep timezone-naive source clock and unlabeled source amount units. | Prevents false timezone/currency interpretation. |

No approval is assumed merely because a formula appears in this design. D01–D05 have concrete defaults so implementation can proceed immediately after review; D06 can remain documented as a source limitation if no further evidence exists.

## Risk register

| Risk | Impact | Control |
|---|---|---|
| Equal-time rows update each other | temporal leakage | compute complete card-time batch before commit; adversarial tie test |
| Late online event or partial tie group | batch/online mismatch | watermark/atomic group or reject and replay from checkpoint |
| Validation/test non-target history unavailable in deployment | offline/online mismatch | D01 decision and explicit observed-event availability policy |
| Byte hashes in older handoff are stale | false artifact mismatch | use current checksum sidecar and semantic split hash independently |
| Unlimited novelty sets consume memory | high RAM | profile unique pairs; do not truncate silently |
| Unknown timezone/currency | misleading hour/amount interpretation | source-relative units; D06 |
| Imputation or encoding fit on all splits | leakage | Tú fits train only; verify transform boundary |
| Dirty Git/LFS status and unreviewed test fix | unsafe handoff | preserve existing changes, review before commit; T01 creates only docs |

## T02 entry checklist

- [ ] Trung/team resolve D01–D05 or record approved alternatives; D06 documented.
- [ ] Recheck branch, HEAD, working tree, LFS state, and upstream inputs in a normal Git environment.
- [ ] Pin feature-definition version, schema/split hash, current processed/manifest byte hashes, and output contract.
- [ ] Implement input validation and all adversarial leakage cases from the architecture document on synthetic data.
- [ ] Demonstrate keyed one-to-one output, strict past-only semantics, same-timestamp batch commit, and split continuity.
- [ ] Verify offline/online state semantics and late-event handling.
- [ ] Profile memory/time before full-dataset feature build; do not infer performance from design alone.
- [ ] Hand a stable train/validation/test feature contract to Tú/Tùng/Khoa; no model training in Trung's feature build.

**Conclusion: `NEEDS_DECISION`.** T01 defines 10/10 features and a feasible architecture, but the proposed behavior and model handoff contract need approval before T02. This document does not certify an implemented feature pipeline.
