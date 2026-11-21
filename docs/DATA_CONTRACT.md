# Data contract

> **Status: validated for local model development.** Full-file checks designate `trans_date_trans_time` as canonical and verify the stable stale-time pattern in `unix_time`. The separate Git LFS tracking issue still blocks a clean repository handoff.

## Normalized table

The canonical dataset is `data/processed/transactions.parquet`, with one row per transaction and a unique, non-null `trans_num`. The field definitions live in `configs/data_schema.yaml`. Its required join fields are `trans_num`, `cc_num`, `timestamp`, `amt`, `category`, `merchant`, and `is_fraud`.

The canonical `timestamp` is parsed from `trans_date_trans_time` and remains timezone-naive because the source declares no timezone. In both complete files, every row is reconstructed exactly by converting `unix_time` from epoch seconds to UTC and adding seven calendar years. Its Unix range is 2012–2013 while the canonical event range is 2019–2020; audit code `UNIX_TIME_STALE_BY_7_CALENDAR_YEARS` records this as a warning. `unix_time` is excluded from normalized Parquet and model features; raw CSV values remain unchanged. `source_dataset` is metadata (`fraudTrain` or `fraudTest`), never a model feature. Names, surname, and street address are removed from the normalized table. `cc_num` remains a string solely to associate observed card history and must not be passed directly to a model.

## Join and prediction interfaces

- Join transaction-level outputs on `trans_num`, never on DataFrame index.
- Each feature output must have exactly one row per `trans_num`; validate one-to-one joins.
- Trung's feature module receives the normalized table and `data/splits/split_manifest.parquet`; its output retains `trans_num`.
- Tu's modeling interface is `train(config, X_train, y_train)` and `predict_score(X)`. Scores correspond to fraud and must be keyed back to `trans_num`.
- Tùng may apply sampling or class weights to train only. Validation and test remain unmodified.
- Khoa's prediction contract is `trans_num, model_id, score, split`; experiment metadata includes threshold, seed, feature_set, strategy, commit hash, and split hash.

## Leakage rules

For an event at time `t`, behavioral features can use only transactions for the same card with timestamp strictly less than `t`. Events sharing a timestamp are a single group: compute all features from history before the group, then update history. Never use a future transaction, equal-time event, `is_fraud` in history, or statistics fitted on validation/test. Observed past train events may be used when producing validation/test features. The current row's non-target fields may be used for transaction-local features.

## Baseline feature set

See `configs/base_features.yaml`: `amt`, calendar fields, `age_at_transaction`, `merchant_distance_km`, `merchant`, and `category`. ID, target, source metadata, and direct identity fields are excluded. Encoding and imputation must be fit on train only. The straight-line merchant distance is a geographic proxy, not a travel distance.

## Missing values and changes

Fields marked nullable may remain missing in the canonical table. Do not drop rows or fit imputation statistics over all splits. Any schema or interface changes should be proposed to the group before downstream modules rely on them.
