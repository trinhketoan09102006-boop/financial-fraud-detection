# Data preprocessing report

## Outcome

- Rows before: 1,852,394 (no transactions removed).
- Rows after: 1,852,394.
- Unique, non-null `trans_num`: 1,852,394.
- Timestamp range: 2019-01-01 00:00:18 to 2020-12-31 23:59:34.
- Canonical time: parsed from `trans_date_trans_time` as timezone-naive; no UTC conversion was applied.
- Source `unix_time`: verified to be exactly seven calendar years behind the text timestamp, so it is excluded from normalized Parquet. The raw field and CSVs are unchanged.
- Row order: stable ascending `timestamp`, then `trans_num` for deterministic ordering only; the ID is not treated as chronology.
- Missing values: 0; no imputation was performed.
- Parquet compression: Zstandard.

## Transformations

- Dropped redundant index and direct identity/address fields: Unnamed: 0 (redundant CSV index), first, last, street, unix_time (stale by seven calendar years).
- Kept source dataset label as metadata: `source_dataset`.
- Parsed `timestamp` from `trans_date_trans_time` and parsed `dob`; kept `cc_num` and `zip` as strings, `trans_num` as the unique row key, and `is_fraud` as integer 0/1.
- Added transaction-local calendar features and `age_at_transaction`.
- Added `merchant_distance_km` as straight-line great-circle distance between profile and merchant coordinates. This is not actual travel distance.
- No sampling, imputation, outlier removal, rolling features, card-history features, or use of future transactions.

## Output fields

`timestamp, cc_num, merchant, category, amt, gender, city, state, zip, lat, long, city_pop, job, dob, trans_num, merch_lat, merch_long, is_fraud, hour, day_of_week, month, is_weekend, age_at_transaction, merchant_distance_km, source_dataset`

## Limitations

- Source timestamps do not declare a timezone. `unix_time` is excluded from the normalized table after exact seven-calendar-year reconstruction across all rows; it remains unchanged in the raw files and is used only for audit diagnostics.
- `source_dataset` identifies whether a row came from the original train or test file; exclude it from model features.
- Merchant distance is a geographic proxy and may not reflect a customer's actual location at transaction time.
