# T01 — Feature contract and architecture

> **APPROVED_FOR_T02:** Trung đã phê duyệt D01–D06 ngày 24/11/2026 trong yêu cầu S1-T02. Các dòng đề xuất hoặc chờ quyết định bên dưới là lịch sử T01; quyết định được duyệt trong yêu cầu T02 có hiệu lực.

**Scope:** proposed interface and algorithm only. No `src/features/` implementation, feature Parquet, training, or data-pipeline change is part of T01. The normative upstream contract is `docs/DATA_CONTRACT.md` with `configs/data_schema.yaml`, `configs/split.yaml`, and `data/splits/split_metadata.json`. The ten formulas and missing rules are in `S1_T01_FEATURE_DICTIONARY.md`. Items marked **proposed** require Trung/team approval before T02.

## Inputs and validation

| Input | Path | Required content |
|---|---|---|
| Normalized transaction table | `data/processed/transactions.parquet` | one row per non-null unique string `trans_num`; string `cc_num`, string `merchant`, string `category`; timezone-naive `timestamp[ns]`; float64 `amt`; `source_dataset` for audit only |
| Assignment | `data/splits/split_manifest.parquet` | exactly one `trans_num, split` row per transaction; `split` in `{train,validation,test}` |
| Split config/metadata | `configs/split.yaml`, `data/splits/split_metadata.json` | matching `nearest_row_count`, counts, cutoff, raw hashes, and semantic split hash `aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8` |
| Field contract | `configs/data_schema.yaml` | source field types and nullability |

Reject duplicate/missing IDs, duplicate manifest assignments, unmatched IDs, invalid split names, null card/timestamp, non-finite amount, invalid timestamp dtype, or a split hash mismatch. Preserve string card IDs exactly; do not cast to integer. `is_fraud` may be present in the normalized table for downstream target join but must be removed from the feature computation view and never enter historical state. Likewise `source_dataset` and split name are metadata, not model predictors. `unix_time` is not a normalized input. Canonical time is parsed from `trans_date_trans_time`; do not derive behavioral time from raw `unix_time` or infer a timezone.

`src/data/split.py` creates train/validation from `source_dataset=fraudTrain`, using a timestamp-grouped `nearest_row_count` boundary. Test is the complete, later `fraudTest` source. It sorts by `timestamp`, with `trans_num` only as deterministic tie-breaker. Across this dataset train max < validation min < test min; no timestamp group crosses a split. Feature calculation must still enforce strict `< anchor timestamp` rather than relying on split membership.

## Public interface and outputs — proposed

```text
build_behavioral_features(transactions, split_manifest, config) -> FeatureBuildResult
```

`transactions` and `split_manifest` are validated in-memory tables or paths; `config` contains schema/split hash and feature-definition version. `FeatureBuildResult` carries a single feature table and metadata. No interface currently exists under `src/features/` beyond `.gitkeep`; this signature is a proposed T02 contract.

Feature table columns, in fixed order: `trans_num`, `txn_count_1h`, `txn_count_24h`, `txn_count_7d`, `hist_amt_mean`, `hist_amt_std`, `amt_ratio`, `txn_recency`, `is_new_merchant`, `is_new_category`, `hour_deviation`. One row per input transaction, unique/non-null `trans_num`, no labels. Use int32 for three counts; float64 for all other ten-minus-three values, with NaN for undefined values. No `cc_num` in model-ready output. Compute into a separate location such as `data/features/behavioral_v1/{train,validation,test}.parquet` (**proposed**); never overwrite processed data or the split manifest. A keyed `trans_num,split` mapping may be stored alongside feature data for audit, but `split` is not part of `X`. For each split, either filter the single computed table by the validated manifest or write a corresponding keyed partition; check one-to-one row coverage and expected counts. Do not compute each split in isolation and reset state.

Metadata sidecar (**proposed**) should include feature-definition version and ordered names/dtypes, split hash and counts, input processed/manifest SHA-256, schema/config version, source code commit or dirty-worktree identifier, UTC generation time (metadata only), null policy, hour-deviation epsilon, algorithm/state version, and output checksums. These are reproducibility metadata; no assumption of source timezone is implied. Record semantic split hash separately from byte hashes, which can change after Parquet rewrite.

## Causal state machine

1. Validate all inputs and manifest. Sort globally by `(timestamp, cc_num, trans_num)` or per card by `(timestamp, trans_num)`; the ID order is only for deterministic output, never an event order within equal timestamps.
2. For each card and timestamp group, read the card state as it existed immediately before `t`. Emit features for every row in the group. Current row `amt` is permitted only as F06 numerator; current merchant/category are permitted only as membership queries; current timestamp is permitted for window and hour queries.
3. Only after all group outputs are fixed, update the card state with every group row. Never add `is_fraud`, prediction, model score, or fitted validation/test statistic to state.
4. Preserve the same card state across train, validation, and test. This is the **proposed observed-history policy**: once a transaction has occurred, its non-target fields may update future state, including a prior validation transaction when scoring later validation/test. The upstream contract explicitly permits past train -> validation/test; it does not explicitly settle every validation -> test deployment scenario. Confirm availability and this broader policy before T02.
5. Enforce event-time order for online updates. On a late/out-of-order event, reject it or rebuild/replay affected future features from a checkpoint; never silently insert it into current state and claim old feature values remain valid. Offline batch sort is allowed. A timestamp group needs a completion/watermark rule online; until complete, defer state commit or document that late same-time arrivals trigger replay.

State per card: last committed timestamp; a deque of timestamp-group counts for the past 7 days (with 1h/24h/7d moving boundaries or three queues); running `(n,mean,M2)` for amount; seen merchant/category sets excluding null; circular-hour `(n,C,S)`. State has no target labels. Persist source-time semantics, schema/version, a stable checkpoint timestamp, and state checksums so online inference and offline replay use identical formulas. If retention of unlimited historical sets or moments is operationally unacceptable, a window/expiry change is a new feature version, not an invisible optimization.

## Leakage invariants and parity

For anchor `(c,t)`, historical membership is `cc_num=c AND timestamp<t`. Count windows additionally require `timestamp>=t-duration`. All equal-time events for a card see identical prior state; different current fields can still yield different F06/F08/F09/F10. Do not fit encoders, imputers, scalers, thresholds, or hyperparameters on validation/test. Do not include ID, card ID, target, source dataset, raw stale Unix time, or split flag in model matrix. Use the same feature definition in offline batch and online service; snapshots/checkpoints must be replayable in timestamp-group order. `source_dataset` is retained only for lineage and test-source verification.

## Performance design

Sort 1,852,394 records once by time/card/ID, O(N log N) time and O(N) temporary index/table storage; a card-grouped external sort or partitions can reduce peak RAM if needed. Then scan once, O(N) expected time for bounded queue operations, Welford updates, and hash-set novelty checks. The 7d deque stores only unexpired event timestamps/counts, O(E_7d) across cards. Amount moments and circular sums use O(C) state for C cards. Novelty sets use O(U_m+U_c) state for distinct card-merchant and card-category pairs; this may dominate memory and must be measured. Batched output storage is O(N) if held in memory, or bounded by a chunk size when streamed to a separate artifact. Do not use per-row scans over entire historical data, expanding self-joins, or quadratic rolling windows. Evaluate correctness first on the 300-row synthetic fixture and adversarial mini-cases; profile memory/time on full data in T02. No runtime benchmark is claimed here.

## Leakage and contract stress-test design for T02

Each scenario below is a proposed test. PASS means exact keyed output comparison, including NaN semantics, not merely successful execution.

| Scenario/input | Expected behavior and PASS condition |
|---|---|
| Inject same-card future row after anchor with extreme amount, new merchant/category, different hour | All ten earlier anchor values unchanged. |
| Two same-card rows at same timestamp, distinct IDs and amounts | Both see pre-group counts/mean/std/recency and neither sees other's merchant/category; later timestamp sees both. |
| First event on a new card | Counts 0; F04–F07/F10 NaN; valid novelty flags 1. |
| Interleave another card with extreme values | Original card outputs unchanged; no cross-card state. |
| Card with train event then validation then test events | Validation sees prior train; test sees prior observed train/validation under proposed policy; no later event affects earlier rows. |
| Flip all `is_fraud` values without changing non-target fields | Every behavioral feature remains identical. |
| Permute input row order, including ties | Keyed feature table identical, regardless of order. |
| Duplicate `trans_num` with different or same payload | Validation fails before feature emission; no arbitrary deduplication. |
| Present records out of timestamp order | Offline sort produces same keyed output; online path rejects/replays late events, never silently corrupts state. |
| Null current merchant/category and null historical values | Respective current novelty is NaN; historical null adds no seen value; other features remain valid. |
| Historical amounts with zero mean | F06 NaN; F04 zero and F05 population std per actual history. |
| Prior event at 23:00, anchor 00:00; history at 23:00 and 01:00 | F10 is 1h in first case; circular mean near midnight in second. |
| Events exactly at `t-1h`, `t-24h`, `t-7d` and one nanosecond earlier | Boundary event counts; earlier one does not. |
| Equal timestamps near a split boundary | No timestamp split across partitions; same-time isolation remains independent of manifest sort. |
| New card with an ID matching no manifest row | Build fails on one-to-one coverage, rather than dropping row. |

## Integration handoff for Tú, Tùng, and Khoa

Trung owns causal feature generation, keyed output, schema/null validation, metadata, and leakage tests. Tú joins on `trans_num` with `validate=one_to_one`, obtains `is_fraud` separately from normalized/split data, excludes IDs and metadata from `X`, and fits any imputation/encoding/scaling on train only. Tùng performs sampling or class weighting on train only, preserving validation/test and row linkage. Khoa stores predictions as `trans_num,model_id,score,split` and records threshold, seed, feature set, strategy, commit hash, and the same split hash. Model teams choose their own estimator and treatment of NaNs after train-only fitting; a zero count is a real zero while missing historical statistics are unknown. No training or imbalance procedure is specified or run here.
