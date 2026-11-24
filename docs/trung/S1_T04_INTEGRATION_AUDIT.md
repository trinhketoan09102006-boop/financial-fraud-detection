# T04 — Integration audit

## Smoke test — PASS

Run with `.venv-clean` on all 1,852,394 input records, using workspace `t04_smoke.py`; `src.features.validate_behavioral.validate` first rechecked the metadata, hashes, schema, split hash, input checksums, ID sets, count ordering and no infinities. Normalized input, manifest and the appropriate feature file were merged by `trans_num` with one-to-one validation and exact row counts; each row had a non-null label and correct split. Runtime 56.13 s.

| Split | Rows | Label 0 | Label 1 | Behavioral NaN cells |
|---|---:|---:|---:|---:|
| train | 1,037,340 | 1,031,372 | 5,968 | 4,820 |
| validation | 259,335 | 257,797 | 1,538 | 95 |
| test | 555,719 | 553,574 | 2,145 | 80 |

All X/y shapes align. Baseline-only has nine columns from `configs/base_features.yaml`, behavioral-only has ten in T01 order, combined has 19, without name collisions. `trans_num`, `cc_num`, `is_fraud`, `source_dataset`, `split`, `timestamp`, `dob`, `unix_time` are excluded from X. X/y were constructed in memory; no model fitting or data resampling occurred. The prediction linkage smoke constructed a small keyed frame containing `trans_num`, split, model ID placeholder, feature version and split hash; no score or model evaluation was generated.

## Team compatibility and missing policy

`src/models`, `src/imbalance`, and `src/evaluation` contain only `.gitkeep`: compatibility with Tú/Tùng/Khoa is **schema/interface-level**, not an executed integration with their code. Tú can fit an estimator-specific imputer/encoder/scaler on train only, preserve NaNs in source artifacts, then apply to validation/test. Count 0 is observed zero, not missing history. Obtain labels independently and keep keys outside X. Tùng should resample only training X/y after causal feature generation; do not recompute features from resampled rows. Khoa should associate scores with `trans_num, model_id, score, split`, record feature version and split hash.

## Temporal contract

D01 allows earlier observed non-target train/validation/test events in subsequent histories, strictly timestamp < anchor; same-card equal-time groups are committed after all features are computed. Existing feature regression tests pass future-injection, label-independence, ties, ordering and cross-split cases. T03 checked all 44 observed equal-time groups. Do not use labels or fit global transforms on validation/test; do not calculate isolated splits with reset state. **DEPLOYMENT_POLICY_REVIEW_PENDING:** online system must provide observed events in chronological order; late/equal-time arrivals need a watermark and reject or replay policy. Online inference itself is not implemented or tested here.

Regression: 23 passed, 0 skipped, 606 warnings, 59.76 s. Artifact and observed local input integrity PASS. Git status remains unresolved; see Git audit.
